# -*- coding: utf-8 -*-
"""
实时数据流推送模块
支持 ACMI 格式数据通过 TCP 输出给 Tacview

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
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Callable

from blade.utils.PlaybackRecorder import ACMI_TYPE_MAPPING, ACMI_COLOR_MAPPING

# Tacview 实时遥测协议常量
TACVIEW_HANDSHAKE_LINE1 = "XtraLib.Stream.0\n"
TACVIEW_HANDSHAKE_LINE2 = "Tacview.RealTimeTelemetry.0\n"
TACVIEW_HANDSHAKE_TERMINATOR = "\0"


@dataclass
class StreamConfig:
    """流式传输配置"""
    acmi_host: str = "127.0.0.1"
    acmi_port: int = 42666
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
            print(f"[ACMI Encoder] 编码错误: {e}")

        return ""


class TCPACMIServer:
    """TCP ACMI 服务器，实现 Tacview 实时遥测协议

    协议流程：
    1. 客户端连接
    2. 服务器发送握手：XtraLib.Stream.0\\nTacview.RealTimeTelemetry.0\\nHost用户名\\n\\0
    3. 客户端回复握手：XtraLib.Stream.0\\nTacview.RealTimeTelemetry.0\\nClient用户名\\n密码哈希\\0
    4. 握手成功后，服务器开始发送 ACMI 数据
    """

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

            print(f"[TCPACMI] ✓ TCP 服务器启动: {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[TCPACMI] ✗ 启动失败: {e}")
            return False

    def _build_host_handshake(self) -> bytes:
        """构建 Host 握手数据包

        根据 Tacview 协议，服务器握手格式为：
            XtraLib.Stream.0\\n
            Tacview.RealTimeTelemetry.0\\n
        """
        handshake = (
            TACVIEW_HANDSHAKE_LINE1
            + TACVIEW_HANDSHAKE_LINE2
        )
        return handshake.encode("utf-8")

    def _read_client_handshake(self, client: socket.socket) -> bool:
        """读取并验证客户端握手数据

        客户端握手格式：
            XtraLib.Stream.0\\n
            Tacview.RealTimeTelemetry.0\\n
            Client username\\n
            password_hash\\0

        Returns:
            bool: 握手是否成功
        """
        try:
            client.settimeout(10.0)  # 握手超时 10 秒
            data = b""
            while b"\0" not in data:
                chunk = client.recv(4096)
                if not chunk:
                    print(f"[TCPACMI] 握手失败：客户端断开连接")
                    return False
                data += chunk

            # 解码并分割
            handshake_text = data.decode("utf-8", errors="replace")
            lines = handshake_text.split("\n")

            # 至少需要 3 行：协议1、协议2、用户名（密码哈希可选）
            if len(lines) < 3:
                print(f"[TCPACMI] 握手失败：数据不完整，收到 {len(lines)} 行")
                return False

            # 验证协议版本
            line1 = lines[0].strip()
            line2 = lines[1].strip()
            client_username = lines[2].strip() if len(lines) > 2 else "Unknown"

            if line1 != "XtraLib.Stream.0":
                print(f"[TCPACMI] 握手失败：协议版本不匹配，收到 '{line1}'")
                return False

            if line2 != "Tacview.RealTimeTelemetry.0":
                print(f"[TCPACMI] 握手失败：遥测协议版本不匹配，收到 '{line2}'")
                return False

            print(f"[TCPACMI] ✓ 握手成功，客户端: {client_username}")
            return True

        except socket.timeout:
            print(f"[TCPACMI] 握手超时")
            return False
        except Exception as e:
            print(f"[TCPACMI] 握手异常: {e}")
            return False

    def _accept_clients(self):
        """接受客户端连接并执行握手

        根据 Tacview 协议，握手流程为：
        1. Tacview（客户端）连接
        2. 本程序（服务器）先发送握手
        3. Tacview 收到后回复客户端握手
        4. 本程序读取并验证客户端握手
        5. 握手成功，开始发送 ACMI 数据
        """
        while self._running:
            try:
                client, addr = self._server_socket.accept()
                client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                print(f"[TCPACMI] 新连接: {addr}，开始握手...")

                # 步骤 1：发送服务器握手（服务器先发送）
                host_handshake = self._build_host_handshake()
                try:
                    client.sendall(host_handshake)
                    print(f"[TCPACMI] → 已发送 Host 握手 ({len(host_handshake)} 字节)")
                except Exception as e:
                    print(f"[TCPACMI] ✗ 发送握手失败: {e}")
                    client.close()
                    continue

                # 步骤 2：读取并验证客户端握手回复
                if not self._read_client_handshake(client):
                    print(f"[TCPACMI] ✗ 握手失败，拒绝连接: {addr}")
                    client.close()
                    continue

                # 步骤 3：握手成功，加入客户端列表
                with self._lock:
                    self._clients.append(client)
                    self._client_count += 1
                print(f"[TCPACMI] ✓ 客户端 #{self._client_count} 已就绪: {addr}")

                # 步骤 4：通知上层（发送 ACMI 头部等）
                if self.on_client_ready:
                    try:
                        self.on_client_ready(client)
                    except Exception as e:
                        print(f"[TCPACMI] ✗ 通知上层失败: {e}")

            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    print(f"[TCPACMI] ✗ 接受连接失败: {e}")

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
            for client in self._clients[:]:  # 使用副本遍历
                try:
                    client.sendall(data_bytes)
                    sent_count += 1
                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
                    print(f"[TCPACMI] 客户端断开: {e}")
                    disconnected.append(client)
                except Exception as e:
                    print(f"[TCPACMI] 发送错误: {e}")
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

        print("[TCPACMI] 服务器已停止")


class TCPStreamer:
    """TCP 实时数据流推送器"""

    def __init__(self, config: StreamConfig):
        self.config = config
        self._acmi_encoder = StreamingACMIEncoder()
        self._tcp_server: Optional[TCPACMIServer] = None
        self._step_count: int = 0
        self._header_generated: bool = False
        self._scenario_name: str = "Panopticon Simulation"

    def start(self) -> bool:
        """启动流式传输"""
        self._tcp_server = TCPACMIServer(
            self.config.acmi_host,
            self.config.acmi_port,
            self.config.host_username,
        )
        # 注册客户端就绪回调：握手成功后立即发送 ACMI 头部
        self._tcp_server.on_client_ready = self._on_client_ready
        return self._tcp_server.start()

    def _on_client_ready(self, client_socket: socket.socket):
        """客户端握手成功后，立即发送 ACMI 头部

        根据 Tacview 协议，握手完成后 Host 应立即开始发送 ACMI 数据，
        首先是 FileType/FileVersion 头部，然后是元数据和数据帧。
        """
        if not self._header_generated:
            # 头部还未生成（仿真尚未开始），发送一个最小头部
            # 这样 Tacview 不会因为没有收到数据而超时断开
            minimal_header = (
                "FileType=text/acmi/tacview\n"
                "FileVersion=2.2\n"
                "0,ReferenceTime=2024-01-01T00:00:00Z\n"
                "0,Title=Waiting for simulation data...\n"
                "\n"
            )
            try:
                client_socket.sendall(minimal_header.encode("utf-8"))
                print(f"[TCPACMI] ✓ 已向新客户端发送最小头部（等待仿真数据）")
            except Exception as e:
                print(f"[TCPACMI] ✗ 发送头部失败: {e}")
            return

        header = self._acmi_encoder.header
        if header:
            try:
                client_socket.sendall(header.encode("utf-8"))
                print(f"[TCPACMI] ✓ 已向新客户端发送 ACMI 头部 ({len(header)} 字节)")
            except Exception as e:
                print(f"[TCPACMI] ✗ 发送头部失败: {e}")

    def stream_step(self, scenario_data: Dict[str, Any], scenario_time: int):
        """流式推送单步数据"""
        self._step_count += 1
        if self._step_count % self.config.send_interval != 0:
            return

        self._send_acmi(scenario_data, scenario_time)

    def _send_acmi(self, scenario_data: Dict[str, Any], scenario_time: int):
        """通过 TCP 发送 ACMI 数据"""
        try:
            # 检查是否有客户端连接
            if self._tcp_server and self._tcp_server.client_count == 0:
                if self._step_count % 100 == 0:
                    print(f"[TCPACMI] 等待 Tacview 连接...")
                return

            # 首次调用时生成头部
            if not self._header_generated:
                current_scenario = scenario_data.get("currentScenario", {})
                self._scenario_name = current_scenario.get("name", "Panopticon Simulation")
                self._acmi_encoder.encode_header(self._scenario_name, scenario_time)
                self._header_generated = True
                print(f"[TCPACMI] ACMI 头部已生成: {self._scenario_name}")

            # 编码当前步的数据帧
            acmi_body = self._acmi_encoder.encode_step(scenario_data, scenario_time)

            if not acmi_body:
                return

            # 调试：打印发送的数据
            if self._step_count <= 5 or self._step_count % 50 == 0:
                print(f"\n[TCPACMI] === 步骤 {self._step_count} ===")
                print(f"[TCPACMI] 客户端数: {self._tcp_server.client_count}")
                print(f"[TCPACMI] 数据帧长度: {len(acmi_body)} 字节")
                print(f"[TCPACMI] 内容预览:")
                for line in acmi_body.split("\n")[:10]:
                    if line.strip():
                        print(f"  {line}")

            if self._tcp_server:
                sent = self._tcp_server.send(acmi_body)
                if sent > 0 and self._step_count % 50 == 0:
                    print(f"[TCPACMI] ✓ 已发送到 {sent} 个客户端")
                elif sent == 0 and self._tcp_server.client_count > 0:
                    print(f"[TCPACMI] ⚠ 发送失败，但有 {self._tcp_server.client_count} 个客户端")
        except Exception as e:
            print(f"[TCPACMI] ✗ 发送失败: {e}")

    def stop(self):
        """停止流式传输"""
        if self._tcp_server:
            self._tcp_server.stop()
        print("[TCPStreamer] 已停止")
