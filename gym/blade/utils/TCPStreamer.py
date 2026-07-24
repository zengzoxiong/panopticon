# -*- coding: utf-8 -*-
"""
实时数据流推送模块
支持 ACMI 格式数据通过 TCP 输出给 Tacview
支持 JSON 格式数据通过 WebSocket 输出给前端

异步双通道架构：
- TCP:42674 - ACMI 格式（Tacview）
- WebSocket:8765 - JSON 格式（前端）
- 两个通道独立运行，互不干涉，同时输出同一时刻的数据流

Tacview 实时遥测协议（完整流程）：
1. 本程序作为 TCP 服务器（Host），Tacview 作为客户端连接
2. 连接建立后，双方进行握手（Handshake）：
   - Host 发送：XtraLib.Stream.0\\nTacview.RealTimeTelemetry.0\\nHost用户名\\n\\0
   - Client 回复：XtraLib.Stream.0\\nTacview.RealTimeTelemetry.0\\nClient用户名\\n密码哈希\\0
3. 握手成功后，Host 发送 ACMI 文件头部 + 元数据
4. 之后按时间步持续发送 ACMI 数据帧
参考文档：https://raia-software-inc.gitbook.io/tacview/technical-documentation/real-time-telemetry-public-protocol
"""

import socket
import threading
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Callable, Set
from http.server import HTTPServer, SimpleHTTPRequestHandler
import asyncio
import websockets

from blade.utils.PlaybackRecorder import ACMI_TYPE_MAPPING, ACMI_COLOR_MAPPING

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('TCPStreamer')

# Tacview 实时遥测协议常量
TACVIEW_HANDSHAKE_LINE1 = "XtraLib.Stream.0\n"
TACVIEW_HANDSHAKE_LINE2 = "Tacview.RealTimeTelemetry.0\n"
TACVIEW_HANDSHAKE_TERMINATOR = "\0"


@dataclass
class StreamConfig:
    """流式传输配置"""
    acmi_host: str = "127.0.0.1"
    acmi_port: int = 42674  # Tacview 默认端口
    ws_host: str = "127.0.0.1"
    ws_port: int = 8765  # WebSocket 默认端口
    send_interval: int = 1  # 每 N 步发送一次
    host_username: str = "Panopticon BLADE"


class StreamingACMIEncoder:
    """流式 ACMI 编码器（参考 PlaybackRecorder 实现）"""

    def __init__(self):
        self._header: str = ""  # 缓存已生成的头部
        self._object_map: Dict[str, int] = {}  # UUID -> ACMI ID
        self._next_id: int = 0x100
        self._start_time: int = 0  # 起始时间（毫秒）

    def _get_acmi_id(self, uuid_str: str) -> int:
        """获取或生成 ACMI 对象 ID"""
        if uuid_str not in self._object_map:
            self._object_map[uuid_str] = self._next_id
            self._next_id += 1
        return self._object_map[uuid_str]

    def _map_class_to_acmi_type(self, class_name: str) -> str:
        """将项目类型名称映射为 ACMI 标准类型"""
        return ACMI_TYPE_MAPPING.get(class_name, "Air+FixedWing")

    def _map_color_to_acmi(self, side_color: str) -> str:
        """将阵营颜色映射为 ACMI 颜色"""
        return ACMI_COLOR_MAPPING.get(side_color.lower(), "Grey")

    def _extract_entity_acmi(self, entity: Dict[str, Any], entity_type: str) -> str:
        """提取单个实体的 ACMI 数据行"""
        if not entity.get("id"):
            return ""

        # 过滤无效位置的实体（位置为 0,0 表示未初始化）
        latitude = entity.get("latitude", 0)
        longitude = entity.get("longitude", 0)
        if latitude == 0 and longitude == 0:
            return ""

        acmi_id = self._get_acmi_id(entity["id"])
        altitude = entity.get("altitude", 0)
        heading = entity.get("heading", 0)
        # ACMI 六元组：T=经度|纬度|高度|滚转|俯仰|偏航
        # 格式: T=lon|lat|alt|roll|pitch|yaw
        coords = f"T={longitude}|{latitude}|{altitude}|||{heading}"

        # 基本属性
        class_name = entity.get("className", entity_type)
        acmi_type = self._map_class_to_acmi_type(class_name)
        color = self._map_color_to_acmi(entity.get("sideColor", ""))
        name = entity.get("name", f"{entity_type}_{acmi_id}")

        # 构建 ACMI 属性字符串
        parts = [
            f"{acmi_id:X}",  # 十六进制 ID
            coords,
            f"Type={acmi_type}",
            f"Color={color}",
            f"Name={name}",
        ]

        # 可选属性
        if entity.get("speed"):
            parts.append(f"TAS={entity['speed']}")
        if entity.get("currentFuel") and entity.get("maxFuel"):
            fuel_percent = int(entity["currentFuel"] / entity["maxFuel"] * 100)
            parts.append(f"Fuel={fuel_percent}%")

        return ",".join(parts)

    @property
    def header(self) -> str:
        """获取已缓存的头部"""
        return self._header

    def encode_header(self, scenario_name: str, scenario_time: int) -> str:
        """编码 ACMI 文件头（只调用一次，结果会被缓存）"""
        from datetime import datetime, timezone
        self._start_time = scenario_time
        ref_time = datetime.fromtimestamp(scenario_time / 1000.0, tz=timezone.utc)
        ref_time_str = ref_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        self._header = (
            "FileType=text/acmi/tacview\n"
            "FileVersion=2.2\n"
            f"0,ReferenceTime={ref_time_str}\n"
            f"0,Title={scenario_name}\n"
            "0,Author=Panopticon BLADE\n"
            "0,DataSource=Panopticon Simulation\n"
            "\n"
        )
        return self._header

    def encode_step(self, scenario_data: Dict[str, Any], scenario_time: int) -> str:
        """编码单个时间步为 ACMI 格式（仅数据帧，不含头部）"""
        if not self._header:
            return ""

        # 计算相对时间（秒）
        relative_time = (scenario_time - self._start_time) / 1000.0
        lines = [f"#{relative_time}"]

        try:
            current_scenario = scenario_data.get("currentScenario", scenario_data)

            # 处理空军基地中的飞机
            for airbase in current_scenario.get("airbases", []):
                for aircraft in airbase.get("aircraft", []):
                    acmi_line = self._extract_entity_acmi(aircraft, "Aircraft")
                    if acmi_line:
                        lines.append(acmi_line)
                    for weapon in aircraft.get("weapons", []):
                        weapon_acmi = self._extract_entity_acmi(weapon, "Weapon")
                        if weapon_acmi:
                            lines.append(weapon_acmi)

                # 处理基地本身
                if airbase.get("id"):
                    airbase_copy = airbase.copy()
                    airbase_copy["className"] = "Airbase"
                    airbase_copy["altitude"] = 0
                    acmi_line = self._extract_entity_acmi(airbase_copy, "Airbase")
                    if acmi_line:
                        lines.append(acmi_line)

            # 处理飞行中的飞机
            for aircraft in current_scenario.get("aircraft", []):
                acmi_line = self._extract_entity_acmi(aircraft, "Aircraft")
                if acmi_line:
                    lines.append(acmi_line)
                for weapon in aircraft.get("weapons", []):
                    weapon_acmi = self._extract_entity_acmi(weapon, "Weapon")
                    if weapon_acmi:
                        lines.append(weapon_acmi)

            # 处理舰艇
            for ship in current_scenario.get("ships", []):
                acmi_line = self._extract_entity_acmi(ship, "Ship")
                if acmi_line:
                    lines.append(acmi_line)

            # 处理顶层武器（已发射的武器）
            for weapon in current_scenario.get("weapons", []):
                acmi_line = self._extract_entity_acmi(weapon, "Weapon")
                if acmi_line:
                    lines.append(acmi_line)

            # 处理设施
            for facility in current_scenario.get("facilities", []):
                facility_copy = facility.copy()
                facility_copy["altitude"] = 0
                acmi_line = self._extract_entity_acmi(facility_copy, "Facility")
                if acmi_line:
                    lines.append(acmi_line)
                for weapon in facility.get("weapons", []):
                    weapon_acmi = self._extract_entity_acmi(weapon, "Weapon")
                    if weapon_acmi:
                        lines.append(weapon_acmi)

            if len(lines) > 1:
                return "\n".join(lines) + "\n"
        except Exception as e:
            logger.error(f"ACMI 编码错误: {e}")

        return ""


class TCPACMIServer:
    """TCP ACMI 服务器，实现 Tacview 实时遥测协议"""

    def __init__(self, host: str, port: int, host_username: str = "Panopticon BLADE"):
        self.host = host
        self.port = port
        self.host_username = host_username
        self._server_socket: Optional[socket.socket] = None
        self._clients: List[socket.socket] = []
        self._lock = threading.Lock()
        self._running = False
        self._accept_thread: Optional[threading.Thread] = None
        self._client_count: int = 0
        self.on_client_ready: Optional[Callable[[socket.socket], None]] = None

    def start(self) -> bool:
        """启动 TCP 服务器"""
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self._server_socket.bind((self.host, self.port))
            self._server_socket.listen(5)
            self._server_socket.settimeout(1.0)
            self._running = True

            self._accept_thread = threading.Thread(target=self._accept_clients, daemon=True)
            self._accept_thread.start()

            logger.info(f"TCP 服务器启动: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"TCP 启动失败: {e}")
            return False

    def _build_host_handshake(self) -> bytes:
        """构建 Host 握手数据包"""
        handshake = (
            TACVIEW_HANDSHAKE_LINE1
            + TACVIEW_HANDSHAKE_LINE2
            + self.host_username + "\n"
            + TACVIEW_HANDSHAKE_TERMINATOR
        )
        return handshake.encode("utf-8")

    def _read_client_handshake(self, client: socket.socket) -> bool:
        """读取并验证客户端握手数据"""
        try:
            client.settimeout(10.0)
            data = b""
            while b"\0" not in data:
                chunk = client.recv(4096)
                if not chunk:
                    logger.info("握手失败：客户端断开连接")
                    return False
                data += chunk

            handshake_text = data.decode("utf-8", errors="replace")

            if not handshake_text.startswith("XtraLib.Stream.0"):
                logger.info(f"握手失败：协议版本不匹配，收到 '{handshake_text[:50]}'")
                return False

            lines = handshake_text.split("\n")
            client_username = lines[2].strip() if len(lines) > 2 else "Unknown"

            logger.info(f"握手成功，客户端: {client_username}")
            return True

        except socket.timeout:
            logger.info("握手超时")
            return False
        except Exception as e:
            logger.error(f"握手异常: {e}")
            return False

    def _accept_clients(self):
        """接受客户端连接并执行握手"""
        while self._running:
            try:
                client, addr = self._server_socket.accept()
                client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                logger.info(f"新连接: {addr}，开始握手...")

                # 步骤 1：发送服务器握手
                host_handshake = self._build_host_handshake()
                try:
                    client.sendall(host_handshake)
                    logger.info(f"已发送 Host 握手 ({len(host_handshake)} 字节)")
                except Exception as e:
                    logger.error(f"发送握手失败: {e}")
                    client.close()
                    continue

                # 步骤 2：读取并验证客户端握手回复
                if not self._read_client_handshake(client):
                    logger.info(f"握手失败，拒绝连接: {addr}")
                    client.close()
                    continue

                # 步骤 3：握手成功后立即发送 ACMI 头部
                header = "FileType=text/acmi/tacview\nFileVersion=2.2\n"
                try:
                    client.sendall(header.encode("utf-8"))
                    logger.info("已发送 ACMI 头部")
                except Exception as e:
                    logger.error(f"发送 ACMI 头部失败: {e}")
                    client.close()
                    continue

                # 步骤 4：加入客户端列表
                with self._lock:
                    self._clients.append(client)
                    self._client_count += 1
                logger.info(f"客户端 #{self._client_count} 已就绪: {addr}")

                # 步骤 5：通知上层
                if self.on_client_ready:
                    try:
                        self.on_client_ready(client)
                    except Exception as e:
                        logger.error(f"通知上层失败: {e}")

            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"接受连接失败: {e}")

    @property
    def client_count(self) -> int:
        """当前连接的客户端数量"""
        with self._lock:
            return len(self._clients)

    def send(self, data: str) -> int:
        """向所有已握手的客户端发送数据"""
        if not self._running:
            return 0

        sent_count = 0
        disconnected = []

        with self._lock:
            if not self._clients:
                return 0

            data_bytes = data.encode("utf-8")
            for client in self._clients[:]:
                try:
                    client.sendall(data_bytes)
                    sent_count += 1
                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
                    logger.info(f"客户端断开: {e}")
                    disconnected.append(client)
                except Exception as e:
                    logger.error(f"发送错误: {e}")
                    disconnected.append(client)

            for client in disconnected:
                try:
                    client.close()
                except:
                    pass
                if client in self._clients:
                    self._clients.remove(client)

        return sent_count

    def stop(self):
        """停止服务器"""
        self._running = False
        with self._lock:
            for client in self._clients:
                try:
                    client.close()
                except:
                    pass
            self._clients.clear()

        if self._server_socket:
            try:
                self._server_socket.close()
            except:
                pass
            self._server_socket = None

        logger.info("TCP 服务器已停止")


class WebSocketServer:
    """WebSocket 服务器，向前端推送 JSON 格式的实时数据"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self._clients: Set[Any] = set()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self) -> bool:
        """启动 WebSocket 服务器"""
        try:
            self._running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            logger.info(f"WebSocket 服务器启动: ws://{self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"WebSocket 启动失败: {e}")
            return False

    def _run(self):
        """在新线程中运行"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._serve())

    async def _serve(self):
        """WebSocket 服务器主循环"""
        async with websockets.serve(
            self._handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10,
        ):
            logger.info(f"WebSocket 正在监听 ws://{self.host}:{self.port}")
            await asyncio.Future()  # 永远运行

    async def _handle_client(self, websocket):
        """处理新的 WebSocket 客户端连接"""
        self._clients.add(websocket)
        client_addr = websocket.remote_address
        logger.info(f"WebSocket 新客户端: {client_addr}")
        try:
            async for message in websocket:
                pass  # 接收客户端消息（目前不需要处理）
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._clients.discard(websocket)
            logger.info(f"WebSocket 客户端断开: {client_addr}")

    def send(self, data: Dict[str, Any]) -> int:
        """向所有客户端发送 JSON 数据"""
        if not self._running or not self._clients or not self._loop:
            return 0

        json_str = json.dumps(data, ensure_ascii=False)
        sent_count = 0

        # 在事件循环中异步发送
        async def _send_to_all():
            nonlocal sent_count
            if not self._clients:
                return
            tasks = []
            for client in list(self._clients):
                try:
                    tasks.append(client.send(json_str))
                except:
                    pass
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                sent_count = sum(1 for r in results if r is None or not isinstance(r, Exception))

        # 在事件循环中执行
        future = asyncio.run_coroutine_threadsafe(_send_to_all(), self._loop)
        try:
            future.result(timeout=1.0)
        except:
            pass

        return sent_count

    @property
    def client_count(self) -> int:
        """当前连接的客户端数量"""
        return len(self._clients)

    def stop(self):
        """停止服务器"""
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        logger.info("WebSocket 服务器已停止")


class StreamingJSONEncoder:
    """流式 JSON 编码器，将场景数据转换为前端可用的 JSON 格式"""

    def __init__(self):
        self._start_time: int = 0

    def encode_step(self, scenario_data: Dict[str, Any], scenario_time: int, step_count: int) -> Dict[str, Any]:
        """编码单个时间步为 JSON 格式"""
        if self._start_time == 0:
            self._start_time = scenario_time

        # 计算相对时间（秒）
        relative_time = (scenario_time - self._start_time) / 1000.0

        objects = []
        try:
            current_scenario = scenario_data.get("currentScenario", scenario_data)

            # 处理空军基地中的飞机
            for airbase in current_scenario.get("airbases", []):
                for aircraft in airbase.get("aircraft", []):
                    obj = self._extract_entity_json(aircraft, "Aircraft")
                    if obj:
                        objects.append(obj)
                    for weapon in aircraft.get("weapons", []):
                        weapon_obj = self._extract_entity_json(weapon, "Weapon")
                        if weapon_obj:
                            objects.append(weapon_obj)

                # 处理基地本身
                if airbase.get("id"):
                    airbase_copy = airbase.copy()
                    airbase_copy["className"] = "Airbase"
                    airbase_copy["altitude"] = 0
                    obj = self._extract_entity_json(airbase_copy, "Airbase")
                    if obj:
                        objects.append(obj)

            # 处理飞行中的飞机
            for aircraft in current_scenario.get("aircraft", []):
                obj = self._extract_entity_json(aircraft, "Aircraft")
                if obj:
                    objects.append(obj)
                for weapon in aircraft.get("weapons", []):
                    weapon_obj = self._extract_entity_json(weapon, "Weapon")
                    if weapon_obj:
                        objects.append(weapon_obj)

            # 处理舰艇
            for ship in current_scenario.get("ships", []):
                obj = self._extract_entity_json(ship, "Ship")
                if obj:
                    objects.append(obj)

            # 处理顶层武器（已发射的武器）
            for weapon in current_scenario.get("weapons", []):
                obj = self._extract_entity_json(weapon, "Weapon")
                if obj:
                    objects.append(obj)

            # 处理设施
            for facility in current_scenario.get("facilities", []):
                facility_copy = facility.copy()
                facility_copy["altitude"] = 0
                obj = self._extract_entity_json(facility_copy, "Facility")
                if obj:
                    objects.append(obj)
                for weapon in facility.get("weapons", []):
                    weapon_obj = self._extract_entity_json(weapon, "Weapon")
                    if weapon_obj:
                        objects.append(weapon_obj)

        except Exception as e:
            logger.error(f"JSON 编码错误: {e}")

        return {
            "timestamp": scenario_time,
            "relativeTime": relative_time,
            "step": step_count,
            "objects": objects
        }

    def _extract_entity_json(self, entity: Dict[str, Any], entity_type: str) -> Optional[Dict[str, Any]]:
        """提取单个实体的 JSON 数据"""
        if not entity.get("id"):
            return None

        # 过滤无效位置的实体
        latitude = entity.get("latitude", 0)
        longitude = entity.get("longitude", 0)
        if latitude == 0 and longitude == 0:
            return None

        # 基本属性
        class_name = entity.get("className", entity_type)
        acmi_type = ACMI_TYPE_MAPPING.get(class_name, "Air+FixedWing")
        color = ACMI_COLOR_MAPPING.get(entity.get("sideColor", "").lower(), "Grey")
        name = entity.get("name", f"{entity_type}")

        obj = {
            "id": entity["id"],
            "type": acmi_type,
            "name": name,
            "color": color,
            "longitude": longitude,
            "latitude": latitude,
            "altitude": entity.get("altitude", 0),
            "heading": entity.get("heading", 0),
        }

        # 可选属性
        if entity.get("speed"):
            obj["speed"] = entity["speed"]
        if entity.get("currentFuel") and entity.get("maxFuel"):
            obj["fuelPercent"] = int(entity["currentFuel"] / entity["maxFuel"] * 100)

        return obj


class TCPStreamer:
    """TCP + WebSocket 实时数据流推送器

    异步双通道架构：
    - TCP: ACMI 格式（Tacview）
    - WebSocket: JSON 格式（前端）
    - 两个通道独立运行，互不干涉
    """

    def __init__(self, config: StreamConfig):
        self.config = config
        self._acmi_encoder = StreamingACMIEncoder()
        self._json_encoder = StreamingJSONEncoder()
        self._tcp_server: Optional[TCPACMIServer] = None
        self._ws_server: Optional[WebSocketServer] = None
        self._step_count: int = 0
        self._header_generated: bool = False
        self._scenario_name: str = "Panopticon Simulation"

    def start(self) -> bool:
        """启动流式传输（同时启动 TCP 和 WebSocket）"""
        # 启动 TCP 服务器
        self._tcp_server = TCPACMIServer(
            self.config.acmi_host,
            self.config.acmi_port,
            self.config.host_username,
        )
        self._tcp_server.on_client_ready = self._on_tcp_client_ready
        tcp_ok = self._tcp_server.start()

        # 启动 WebSocket 服务器
        self._ws_server = WebSocketServer(
            self.config.ws_host,
            self.config.ws_port,
        )
        ws_ok = self._ws_server.start()

        return tcp_ok or ws_ok

    def _on_tcp_client_ready(self, client_socket: socket.socket):
        """TCP 客户端握手成功后的回调"""
        logger.info("TCP 客户端已就绪，等待仿真数据...")

    def stream_step(self, scenario_data: Dict[str, Any], scenario_time: int):
        """流式推送单步数据（同时推送到 TCP 和 WebSocket）"""
        self._step_count += 1
        logger.debug(f"stream_step 调用: step={self._step_count}, send_interval={self.config.send_interval}")
        if self._step_count % self.config.send_interval != 0:
            return

        # 异步推送到两个通道
        self._send_acmi(scenario_data, scenario_time)
        self._send_json(scenario_data, scenario_time)

    def _send_acmi(self, scenario_data: Dict[str, Any], scenario_time: int):
        """通过 TCP 发送 ACMI 数据"""
        try:
            if self._tcp_server and self._tcp_server.client_count == 0:
                if self._step_count % 100 == 0:
                    logger.info("等待 Tacview 连接...")
                return

            if not self._header_generated:
                current_scenario = scenario_data.get("currentScenario", {})
                self._scenario_name = current_scenario.get("name", "Panopticon Simulation")
                self._acmi_encoder.encode_header(self._scenario_name, scenario_time)
                self._header_generated = True
                logger.info(f"ACMI 头部已生成: {self._scenario_name}")

            acmi_body = self._acmi_encoder.encode_step(scenario_data, scenario_time)

            if not acmi_body:
                return

            if self._step_count <= 5 or self._step_count % 50 == 0:
                logger.info(f"[TCP] 步骤 {self._step_count}, 客户端: {self._tcp_server.client_count}")

            if self._tcp_server:
                sent = self._tcp_server.send(acmi_body)
                if sent > 0 and self._step_count % 50 == 0:
                    logger.info(f"[TCP] 已发送到 {sent} 个客户端")
        except Exception as e:
            logger.error(f"TCP 发送失败: {e}")

    def _send_json(self, scenario_data: Dict[str, Any], scenario_time: int):
        """通过 WebSocket 发送 JSON 数据"""
        try:
            logger.debug(f"[WS] _send_json 调用: step={self._step_count}")
            if self._ws_server and self._ws_server.client_count == 0:
                if self._step_count % 100 == 0:
                    logger.info("等待前端 WebSocket 连接...")
                return

            json_data = self._json_encoder.encode_step(scenario_data, scenario_time, self._step_count)

            if not json_data or not json_data.get("objects"):
                return

            if self._step_count <= 5 or self._step_count % 50 == 0:
                logger.info(f"[WS] 步骤 {self._step_count}, 客户端: {self._ws_server.client_count}, 对象: {len(json_data['objects'])}")

            if self._ws_server:
                sent = self._ws_server.send(json_data)
                if sent > 0 and self._step_count % 50 == 0:
                    logger.info(f"[WS] 已发送到 {sent} 个客户端")
        except Exception as e:
            logger.error(f"WebSocket 发送失败: {e}")

    def stop(self):
        """停止流式传输"""
        if self._tcp_server:
            self._tcp_server.stop()
        if self._ws_server:
            self._ws_server.stop()
        logger.info("TCPStreamer 已停止")
