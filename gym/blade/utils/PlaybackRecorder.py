# -*- coding: utf-8 -*-
"""
PlaybackRecorder - 仿真录制器

负责将仿真过程记录为 JSONL 和 ACMI 两种格式文件：
- JSONL 格式：每行一个 JSON 对象，记录某一时刻的仿真快照，支持前端回放
- ACMI 格式：Tacview 兼容格式，支持专业 3D 态势分析工具
"""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from blade.Scenario import Scenario
from blade.utils.utils import unix_to_local_time

# 文件大小限制（MB），超过此大小会自动分片导出
FILE_SIZE_LIMIT_MB = 10
# 字符数限制，对应 FILE_SIZE_LIMIT_MB 的字节数
CHARACTER_LIMIT = FILE_SIZE_LIMIT_MB * 1024 * 1024
# 默认录制间隔（秒），每隔多少秒记录一次快照
RECORDING_INTERVAL_SECONDS = 10

# ACMI 对象类型映射：项目类型名称 -> ACMI 标准类型
ACMI_TYPE_MAPPING = {
    # 飞机类型
    "F-35A Lightning II": "Air+FixedWing",
    "F/A-18E Super Hornet": "Air+FixedWing",
    "Su-27": "Air+FixedWing",
    "MiG-29": "Air+FixedWing",
    "B-52H Stratofortress": "Air+FixedWing+Heavy",
    "KC-135R Stratotanker": "Air+FixedWing+Tanker",
    "E-3B Sentry": "Air+FixedWing+AWACS",
    # 舰艇类型
    "Arleigh Burke DDG": "Sea+Ship+Destroyer",
    "Ticonderoga CG": "Sea+Ship+Cruiser",
    "Nimitz CVN": "Sea+Ship+Carrier",
    "Virginia SSN": "Sea+Submarine",
    # 防空系统
    "S-400": "Ground+SAM",
    "Patriot": "Ground+SAM",
    "MIM-104": "Ground+SAM",
    # 武器类型
    "Sample Weapon": "Weapon+Missile",
    "Missile": "Weapon+Missile",
    "SAM": "Weapon+Missile",
    # 默认类型
    "Default Aircraft": "Air+FixedWing",
    "Default Ship": "Sea+Ship",
    "Default SAM": "Ground+SAM",
    "Airbase": "Ground+Structure",
    "Facility": "Ground+Structure",
    "ReferencePoint": "Point+Marker",
}

# ACMI 颜色映射
ACMI_COLOR_MAPPING = {
    "blue": "Blue",
    "red": "Red",
    "green": "Green",
    "neutral": "Grey",
}


class PlaybackRecorder:
    """
    仿真录制器类

    将仿真过程按时间间隔记录为 JSONL 和 ACMI 两种格式文件，支持：
    - 按时间间隔自动采样
    - 超大文件自动分片
    - 同时导出 JSONL（前端回放）和 ACMI（Tacview 分析）两种格式

    Attributes:
        scenario_name: 当前录制的想定名称
        current_scenario_time: 上次录制的时间点（Unix时间戳）
        recording: 当前 JSONL 录制内容
        acmi_recording: 当前 ACMI 录制内容
        acmi_object_map: UUID 到 ACMI 对象 ID 的映射
        acmi_next_id: 下一个可用的 ACMI 对象 ID
        recording_start_time: 录制开始时间（Unix时间戳）
        record_every_seconds: 录制间隔（秒）
        recording_export_path: 录制文件导出路径
    """

    def __init__(
        self,
        record_every_seconds: Optional[int] = None,
        recording_export_path: Optional[str] = ".",
        export_acmi: bool = True,
    ) -> None:
        """
        初始化录制器

        Args:
            record_every_seconds: 录制间隔（秒），默认为 RECORDING_INTERVAL_SECONDS
            recording_export_path: 导出路径，默认为当前目录
            export_acmi: 是否同时导出 ACMI 格式，默认为 True
        """
        self.scenario_name: str = "New Scenario"
        self.current_scenario_time: int = 0
        self.recording: str = ""
        self.recording_start_time: int = 0
        self.record_every_seconds: int = (
            record_every_seconds if record_every_seconds else RECORDING_INTERVAL_SECONDS
        )
        self.recording_export_path: str = recording_export_path
        self.export_acmi: bool = export_acmi

        # ACMI 格式相关属性
        self.acmi_recording: str = ""
        self.acmi_object_map: Dict[str, int] = {}  # UUID -> ACMI ID
        self.acmi_next_id: int = 0x100  # 从 256 开始，避免与保留 ID 冲突
        self.acmi_reference_time: Optional[datetime] = None

    def _get_acmi_id(self, uuid_str: str) -> int:
        """
        获取或生成 ACMI 对象 ID

        将 UUID 映射为 ACMI 使用的十六进制 ID。

        Args:
            uuid_str: UUID 字符串

        Returns:
            int: ACMI 对象 ID
        """
        if uuid_str not in self.acmi_object_map:
            self.acmi_object_map[uuid_str] = self.acmi_next_id
            self.acmi_next_id += 1
        return self.acmi_object_map[uuid_str]

    def _map_class_to_acmi_type(self, class_name: str) -> str:
        """
        将项目类型名称映射为 ACMI 标准类型

        Args:
            class_name: 项目中的单位类型名称

        Returns:
            str: ACMI 类型字符串
        """
        return ACMI_TYPE_MAPPING.get(class_name, "Air+FixedWing")

    def _map_color_to_acmi(self, side_color: str) -> str:
        """
        将阵营颜色映射为 ACMI 颜色

        Args:
            side_color: 阵营颜色名称

        Returns:
            str: ACMI 颜色字符串
        """
        return ACMI_COLOR_MAPPING.get(side_color.lower(), "Grey")

    def _init_acmi_header(self, scenario: Scenario) -> str:
        """
        生成 ACMI 文件头部

        Args:
            scenario: 想定对象

        Returns:
            str: ACMI 文件头字符串
        """
        self.acmi_reference_time = datetime.fromtimestamp(
            scenario.current_time, tz=timezone.utc
        )
        ref_time_str = self.acmi_reference_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        header = (
            "FileType=text/acmi/tacview\n"
            "FileVersion=2.2\n"
            f"0,ReferenceTime={ref_time_str}\n"
            f"0,Title={scenario.name}\n"
            "0,Author=Panopticon BLADE\n"
            "0,DataSource=Panopticon Simulation\n"
            "\n"
        )
        return header

    def _extract_entity_acmi(self, entity: Dict[str, Any], entity_type: str) -> str:
        """
        提取单个实体的 ACMI 数据行

        Args:
            entity: 实体数据字典
            entity_type: 实体类型标识（如 "Aircraft", "Ship"）

        Returns:
            str: ACMI 数据行，如果实体无效则返回空字符串
        """
        if not entity.get("id"):
            return ""

        acmi_id = self._get_acmi_id(entity["id"])
        longitude = entity.get("longitude", 0)
        latitude = entity.get("latitude", 0)
        altitude = entity.get("altitude", 0)
        heading = entity.get("heading", 0)
        # ACMI 六元组：经度|纬度|高度|滚转|俯仰|偏航
        # 本项目无滚转和俯仰数据，留空
        coords = f"T={longitude}|{latitude}|{altitude}||{heading}|"

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

    def _convert_snapshot_to_acmi(self, snapshot: Dict[str, Any], relative_time: int) -> str:
        """
        将一个 JSONL 快照转换为 ACMI 格式

        Args:
            snapshot: JSONL 快照数据（已解析为字典）
            relative_time: 相对于录制开始的时间（秒）

        Returns:
            str: ACMI 格式的该时刻数据
        """
        lines = [f"#{relative_time}"]

        scenario = snapshot.get("currentScenario", {})

        # 处理空军基地中的飞机（停在基地中的飞机）
        for airbase in scenario.get("airbases", []):
            for aircraft in airbase.get("aircraft", []):
                acmi_line = self._extract_entity_acmi(aircraft, "Aircraft")
                if acmi_line:
                    lines.append(acmi_line)
                # 处理飞机携带的武器
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

        # 处理飞行中的飞机（不在基地中的飞机）
        for aircraft in scenario.get("aircraft", []):
            acmi_line = self._extract_entity_acmi(aircraft, "Aircraft")
            if acmi_line:
                lines.append(acmi_line)
            # 处理飞机携带的武器
            for weapon in aircraft.get("weapons", []):
                weapon_acmi = self._extract_entity_acmi(weapon, "Weapon")
                if weapon_acmi:
                    lines.append(weapon_acmi)

        # 处理舰艇
        for ship in scenario.get("ships", []):
            acmi_line = self._extract_entity_acmi(ship, "Ship")
            if acmi_line:
                lines.append(acmi_line)

        # 处理顶层武器（已发射的武器）
        for weapon in scenario.get("weapons", []):
            acmi_line = self._extract_entity_acmi(weapon, "Weapon")
            if acmi_line:
                lines.append(acmi_line)

        # 处理设施
        for facility in scenario.get("facilities", []):
            facility_copy = facility.copy()
            facility_copy["altitude"] = 0
            acmi_line = self._extract_entity_acmi(facility_copy, "Facility")
            if acmi_line:
                lines.append(acmi_line)
            # 处理设施携带的武器
            for weapon in facility.get("weapons", []):
                weapon_acmi = self._extract_entity_acmi(weapon, "Weapon")
                if weapon_acmi:
                    lines.append(weapon_acmi)

        # 处理参考点（如果有）
        for ref_point in scenario.get("referencePoints", []):
            if ref_point.get("id"):
                ref_copy = ref_point.copy()
                ref_copy["altitude"] = 0
                ref_copy["className"] = "ReferencePoint"
                acmi_line = self._extract_entity_acmi(ref_copy, "Point")
                if acmi_line:
                    lines.append(acmi_line)

        return "\n".join(lines) + "\n"

    def should_record(self, current_scenario_time: int) -> bool:
        """
        判断当前时刻是否应该录制

        根据距上次录制的时间间隔判断，达到间隔则返回 True。

        Args:
            current_scenario_time: 当前仿真时间（Unix时间戳）

        Returns:
            bool: 是否应该录制
        """
        if (
            current_scenario_time - self.current_scenario_time
            >= self.record_every_seconds
        ):
            self.current_scenario_time = current_scenario_time
            return True
        return False

    def reset(self):
        """
        重置录制器状态

        清空所有录制数据，恢复初始状态。在开始新录制前调用。
        """
        self.scenario_name = "New Scenario"
        self.recording = ""
        self.current_scenario_time = 0
        self.recording_start_time = 0

        # 重置 ACMI 相关状态
        self.acmi_recording = ""
        self.acmi_object_map = {}
        self.acmi_next_id = 0x100
        self.acmi_reference_time = None

    def start_recording(self, scenario: Scenario):
        """
        开始录制

        重置状态并初始化录制参数，从当前想定状态开始录制。

        Args:
            scenario: 当前想定对象，用于获取名称和起始时间
        """
        self.reset()
        self.scenario_name = scenario.name
        self.current_scenario_time = scenario.current_time
        self.recording_start_time = scenario.current_time

        # 初始化 ACMI 文件头
        if self.export_acmi:
            self.acmi_recording = self._init_acmi_header(scenario)

    def record_step(self, current_step: str, current_scenario_time: int):
        """
        记录一步仿真数据

        将当前步骤的 JSON 字符串追加到录制内容中。
        同时转换为 ACMI 格式追加到 ACMI 缓冲区。
        如果录制内容超过文件大小限制，自动导出并清空缓冲区。

        Args:
            current_step: 当前步骤的 JSON 字符串（一行 JSONL）
            current_scenario_time: 当前仿真时间（Unix时间戳）
        """
        # JSONL 录制
        self.recording += current_step + "\n"

        # ACMI 录制
        if self.export_acmi:
            try:
                snapshot = json.loads(current_step)
                relative_time = current_scenario_time - self.recording_start_time
                acmi_step = self._convert_snapshot_to_acmi(snapshot, relative_time)
                self.acmi_recording += acmi_step
            except json.JSONDecodeError:
                pass  # 跳过无效的 JSON 数据

        # 超过大小限制时自动导出分片
        if len(self.recording) > CHARACTER_LIMIT:
            self.export_recording(current_scenario_time, self.recording_start_time)
            self.recording_start_time = current_scenario_time
            self.recording = ""
            # ACMI 分片时重新写入头部
            if self.export_acmi:
                # 保留当前对象映射，但重置录制内容
                # 注意：分片后的 ACMI 文件需要独立的头部
                self.acmi_recording = ""

    def export_recording(
        self,
        recording_end_time_unix: int,
        recording_start_time_unix: Optional[int] = None,
    ):
        """
        导出录制文件

        将录制内容保存为 JSONL 和 ACMI 文件，文件名包含时间范围。

        Args:
            recording_end_time_unix: 录制结束时间（Unix时间戳）
            recording_start_time_unix: 录制开始时间（Unix时间戳），默认使用实例属性
        """
        if not self.recording:
            return

        if recording_start_time_unix is None:
            recording_start_time_unix = self.recording_start_time

        # 格式化时间为可读字符串（用于文件名）
        formatted_recording_start_time = unix_to_local_time(
            recording_start_time_unix, separator=""
        )
        formatted_recording_end_time = unix_to_local_time(
            recording_end_time_unix, separator=""
        )
        suffix = f"{formatted_recording_start_time} - {formatted_recording_end_time}"

        # 导出 JSONL 文件
        jsonl_filename = f"{self.recording_export_path}/{self.scenario_name} Recording {suffix}.jsonl"
        with open(jsonl_filename, "w", encoding="utf-8") as file:
            file.write(self.recording.rstrip("\n"))
        print(f"JSONL recording exported to '{jsonl_filename}'")

        # 导出 ACMI 文件
        if self.export_acmi and self.acmi_recording:
            acmi_filename = f"{self.recording_export_path}/{self.scenario_name} Recording {suffix}.acmi"
            with open(acmi_filename, "w", encoding="utf-8") as file:
                file.write(self.acmi_recording.rstrip("\n"))
            print(f"ACMI recording exported to '{acmi_filename}'")
