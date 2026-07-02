# 观测数据类型

Gymnasium 环境暴露由 Scenario 类在每个时间步定义的观测。该类包含场景的名称、开始时间、持续时间、各方、当前时间、仿真速度（称为时间压缩）、飞机、舰船、设施、空军基地、武器、参考点和任务等参数。观测可以导出为 JSON 文件，上传到 Web 应用程序进行可视化。

## Scenario（场景）

表示仿真时间步（由 currentTime 定义）的整个场景。

### 属性

- `id`：(str) 场景的唯一标识符。
  - 示例："6806c96b-14f8-4c52-ba60-c6d24e238a17"

- `name`：(str) 场景的名称。
  - 示例："Test Scenario"

- `startTime`：(int) 场景的开始时间，Unix 时间戳格式。
  - 示例：1699073110

- `currentTime`：(int) 场景中的当前时间，Unix 时间戳格式。
  - 示例：1699073110

- `duration`：(int) 场景的总持续时间（秒）。
  - 示例：14400

- `timeCompression`：(int) 仿真的运行速度。

- `sides`：(list[Side]) 描述场景中涉及的各方（例如 BLUE、RED）。

- `aircraft`：(list[Aircraft]) 场景中的飞机列表。

- `ships`：(list[Ship]) 场景中的舰船列表。

- `facilities`：(list[Facility]) 场景中的设施列表（例如 SAM）。

- `airbases`：(list[Airbase]) 场景中的空军基地列表。

- `weapons`：(list[Weapon]) 场景中当前部署/发射的武器列表。

- `referencePoints`：(list[ReferencePoint]) 场景中当前的参考点列表。

- `missions`：(list[PatrolMission | StrikeMission]) 场景中的任务列表。

- `relationships`：(Relationships) 场景中各方之间的关系。决定各方是盟友还是敌人。

- `doctrine`：(Doctrine) 定义场景中各方行为的条令。

### 方法

- `toJSON()`：(str) 将此对象作为 JSON 返回。

## Side（方）

此类描述场景中涉及的各方（例如 BLUE、RED）。

### 属性

- `id`：(str) 方的唯一标识符。
  - 示例："47179c9e-aa00-4bba-a784-cec9108fdb4b"

- `name`：(str) 方的名称。
  - 示例："BLUE"

- `totalScore`：(int) 方的总分。
  - 示例：0

- `sideColor`：(str) 表示该方的颜色。
  - 示例："blue"

### 方法

- `toJSON()`：(str) 将此对象作为 JSON 返回。

## Airbase（空军基地）

此类描述空军基地，主要用于停放飞机。

### 属性

- `id`：(str) 空军基地的唯一标识符。
  - 示例："47179c9e-aa00-4bba-a784-cec9108fdb4b"

- `name`：(str) 空军基地的名称。
  - 示例："Andersen AFB"

- `sideName`：(str) 空军基地所属的方。

- `sideColor`：(str) 空军基地当前方的颜色。

- `className`：(str) 空军基地的类型。

- `latitude`：(float) 纬度位置。

- `longitude`：(float) 经度位置。

- `altitude`：(float) 高度（英尺）。

- `aircraft`：(list[Aircraft]) 停放在空军基地的飞机列表。

### 方法

- `toJSON()`：(str) 将此对象作为 JSON 返回。

## Aircraft（飞机）

此类描述一架飞机。

### 属性

- `id`：(str) 飞机的唯一标识符。
  - 示例："7bc96d3b-ffe7-4469-b976-893e7fa5deca"

- `name`：(str) 飞机的名称/呼号。
  - 示例："Beaver #1"

- `sideName`：(str) 飞机所属的方（例如 BLUE、RED）。
  - 示例："BLUE"

- `sideColor`：(str) 飞机当前方的颜色。

- `selected`：(bool) 单位是否当前被选中。

- `className`：(str) 飞机的类型。
  - 示例："F-16C"

- `latitude`：(float) 纬度位置。
  - 示例：20.442558487173827

- `longitude`：(float) 经度位置。
  - 示例：144.16072045098306

- `altitude`：(float) 高度（英尺）。
  - 示例：10000

- `heading`：(float) 航向（度）。
  - 示例：85.42632327325884

- `speed`：(float) 速度（节）。
  - 示例：350

- `currentFuel`：(float) 剩余燃料。
  - 示例：100000

- `maxFuel`：(float) 最大燃料容量。
  - 示例：100000

- `fuelRate`：(float) 燃料消耗率（磅/小时）。

- `weapons`：(list[Weapon]) 飞机拥有的武器列表。

- `range`：(float) 飞机的最大航程。

- `route`：(list[list[float]]) 飞机的当前航线（航路点集合）。

- `homeBaseId`：(str) 飞机所属基地的标识符。

- `rtb`：(bool) 飞机是否正在返回基地。

- `targetId`：(str) 飞机当前目标的标识符。

### 方法

- `getTotalWeaponQuantity()`：(int) 返回飞机当前的武器数量。

- `getWeaponWithHighestRange()`：(int) 返回飞机射程最远的武器。

- `toJSON()`：(str) 将此对象作为 JSON 返回。

## Facility（设施）

此类描述一个设施，通常用于表示地对空导弹（SAM）。

### 属性

- `id`：(str) 设施的唯一标识符。
  - 示例："8dd38f74-7e04-446f-94c7-5f5f82157d49"

- `name`：(str) 设施的名称。
  - 示例："SAM #1"

- `sideName`：(str) 单位所属的方（例如 BLUE、RED）。
  - 示例："BLUE"

- `sideColor`：(str) 单位当前方的颜色。

- `className`：(str) 设施的类型。

- `latitude`：(float) 纬度位置。
  - 示例：20.442558487173827

- `longitude`：(float) 经度位置。
  - 示例：144.16072045098306

- `altitude`：(float) 高度（英尺）。
  - 示例：10000

- `range`：(float) 设施武器的射程（海里）。
  - 示例：250

- `weapons`：(list[Weapon]) 设施拥有的武器列表。

### 方法

- `getTotalWeaponQuantity()`：(int) 返回设施当前的武器数量。

- `getWeaponWithHighestRange()`：(int) 返回设施射程最远的武器。

- `toJSON()`：(str) 将此对象作为 JSON 返回。

## ReferencePoint（参考点）

此类描述可用于定义任务区域的参考点。

### 属性

- `id`：(str) 参考点的唯一标识符。
  - 示例："f2c69876-986f-4eb2-aa09-da00125e0e09"

- `name`：(str) 参考点的名称或标识。
  - 示例："Reference Point #1175"

- `sideName`：(str) 参考点所属的方（例如 BLUE、RED）。
  - 示例："BLUE"

- `sideColor`：(str) 表示与参考点相关联的方的颜色。
  - 示例："blue"

- `latitude`：(float) 参考点的纬度坐标。
  - 示例：21.800061432629548

- `longitude`：(float) 参考点的经度坐标。
  - 示例：149.8482617352473

- `altitude`：(float) 参考点的高度（如果是地面点，通常为 0）。
  - 示例：0

### 方法

- `toJSON()`：(str) 将此对象作为 JSON 返回。

## Ship（舰船）

此类描述一艘舰船，它可以移动也可以停放飞机。

### 属性

- `id`：(str) 舰船的唯一标识符。
  - 示例："7bc96d3b-ffe7-4469-b976-893e7fa5deca"

- `name`：(str) 舰船的名称/呼号。
  - 示例："Carrier #4201"

- `sideName`：(str) 舰船所属的方（例如 BLUE、RED）。
  - 示例："BLUE"

- `sideColor`：(str) 舰船当前方的颜色。

- `selected`：(bool) 单位是否当前被选中。

- `className`：(str) 舰船的类型。
  - 示例："Carrier"

- `latitude`：(float) 纬度位置。
  - 示例：20.442558487173827

- `longitude`：(float) 经度位置。
  - 示例：144.16072045098306

- `altitude`：(float) 高度（英尺）。
  - 示例：10000

- `heading`：(float) 航向（度）。
  - 示例：85.42632327325884

- `speed`：(float) 速度（节）。
  - 示例：350

- `currentFuel`：(float) 剩余燃料。
  - 示例：100000

- `maxFuel`：(float) 最大燃料容量。
  - 示例：100000

- `fuelRate`：(float) 燃料消耗率（磅/小时）。

- `range`：(float) 舰船武器的最大射程。

- `route`：(list[list[float]]) 舰船的当前航线（航路点集合）。

- `weapons`：(list[Weapon]) 舰船拥有的武器列表。

- `aircraft`：(list[Aircraft]) 停放在舰船上的飞机列表。

### 方法

- `getTotalWeaponQuantity()`：(int) 返回舰船当前的武器数量。

- `getWeaponWithHighestRange()`：(int) 返回舰船射程最远的武器。

- `toJSON()`：(str) 将此对象作为 JSON 返回。

## Weapon（武器）

此类描述一种武器，通常用于定义导弹。

### 属性

- `id`：(str) 武器的唯一标识符。
  - 示例："c9065bb1-4b3a-41d5-bc91-a16bdb23881c"

- `name`：(str) 武器的名称。
  - 示例："Sample Weapon"

- `sideName`：(str) 武器所属的方（例如 BLUE、RED）。
  - 示例："BLUE"

- `sideColor`：(str) 武器当前方的颜色。

- `className`：(str) 武器的类型。
  - 示例："AGM-158"

- `latitude`：(float) 纬度位置。
  - 示例：20.442558487173827

- `longitude`：(float) 经度位置。
  - 示例：144.16072045098306

- `altitude`：(float) 高度（英尺）。
  - 示例：10000

- `heading`：(float) 航向（度）。
  - 示例：85.42632327325884

- `speed`：(float) 速度（节）。
  - 示例：350

- `currentFuel`：(float) 剩余燃料。
  - 示例：100000

- `maxFuel`：(float) 最大燃料容量。
  - 示例：100000

- `fuelRate`：(float) 燃料消耗率（磅/小时）。

- `range`：(float) 武器的最大射程。

- `route`：(list[list[float]]) 武器的当前航线（航路点集合）。

- `targetId`：(str) 武器当前目标的标识符。

- `lethality`：(float) 武器的杀伤力分数。用于计算命中目标是否被摧毁。
  - 示例：0.25

- `currentQuantity`：(int) 可用武器数量。
  - 示例：10

- `maxQuantity`：(int) 最大武器数量。
  - 示例：10

### 方法

- `toJSON()`：(str) 将此对象作为 JSON 返回。

## PatrolMission（巡逻任务）

此类描述一个巡逻任务，单位在定义的区域内随机巡逻。

### 属性

- `id`：(str) 任务的唯一标识符。
  - 示例："a8ab936c-184b-42bf-aa83-abca31bb2e73"

- `name`：(str) 任务的名称。
  - 示例："Andersen Patrol"

- `sideId`：(str) 拥有该任务的方。
  - 示例："BLUE"

- `assignedUnitIds`：(list[str]) 分配给任务的单位 ID 列表。
  - 示例：["7bc96d3b-ffe7-4469-b976-893e7fa5deca", "46e0ab0f-b49c-4961-b265-ce93dd163c21"]

- `assignedArea`：(list[ReferencePoint]) 定义巡逻或任务区域的地理坐标。
  - 示例：[[21.800061432629548, 149.8482617352473], [14.753441339796368, 150.96692676017133]]

- `active`：(bool) 任务是否处于活动状态。

### 方法

- `checkIfCoordinatesIsWithinPatrolArea(coordinates: list[float])`：(bool) 如果输入坐标在任务巡逻区域内，则返回 true。

- `generateRandomCoordinatesWithinPatrolArea()`：(list[float]) 在巡逻区域内生成一个随机航路点。

- `toJSON()`：(str) 将此对象作为 JSON 返回。

## StrikeMission（打击任务）

此类描述一个打击任务，一组攻击者打击一组目标。

### 属性

- `id`：(str) 任务的唯一标识符。
  - 示例："a8ab936c-184b-42bf-aa83-abca31bb2e73"

- `name`：(str) 任务的名称。
  - 示例："Liaoning Strike"

- `sideId`：(str) 拥有该任务的方。
  - 示例："BLUE"

- `assignedUnitIds`：(list[str]) 分配给任务的单位 ID 列表。
  - 示例：["7bc96d3b-ffe7-4469-b976-893e7fa5deca", "46e0ab0f-b49c-4961-b265-ce93dd163c21"]

- `assignedTargetIds`：(list[str]) 目标 ID 列表。
  - 示例：["7bc96d3b-ffe7-4469-b976-893e7fa5deca", "46e0ab0f-b49c-4961-b265-ce93dd163c21"]

- `active`：(bool) 任务是否处于活动状态。

### 方法

- `toJSON()`：(str) 将此对象作为 JSON 返回。

## Relationships（关系）

此类描述场景中各方之间的关系，决定各方是盟友还是敌人。

### 属性

- `hostiles`：(Dict[str, List[str]]) 包含各方敌人的映射。
  - 示例：{"12345678-1234-5678-1234-567812345678": ["87654321-4321-4321-4321-123456789012"]}

- `allies`：(Dict[str, List[str]]) 包含各方盟友的映射。
  - 示例：{"12345678-1234-5678-1234-567812345678": ["87654321-4321-4321-4321-123456789012"]}

## Doctrine（条令）

此类描述定义场景中各方行为的条令。

### 属性

- `AIRCRAFT_ATTACK_HOSTILE`：(bool) 飞机是否攻击敌方单位。

- `AIRCRAFT_CHASE_HOSTILE`：(bool) 飞机是否追击敌方单位。

- `AIRCRAFT_RTB_WHEN_OUT_OF_RANGE`：(bool) 飞机在目标超出射程时是否返回基地。

- `AIRCRAFT_RTB_WHEN_STRIKE_MISSION_COMPLETE`：(bool) 打击任务完成后飞机是否返回基地。

- `SAM_ATTACK_HOSTILE`：(bool) 地对空导弹（SAM）是否攻击敌方单位。

- `SHIP_ATTACK_HOSTILE`：(bool) 舰船是否攻击敌方单位。

# 动作数据类型

BLADE 的动作空间由 Game 类提供的函数定义，这些函数修改底层仿真。这些动作可以由代理作为字符串调用。例如，要指挥 ID 为 1 的飞机飞往坐标 (10, 10)，将字符串 `move_aircraft(1, 10, 10)` 作为动作传递到 Gymnasium 环境中。

- `add_reference_point(reference_point_name: str, latitude: float, longitude: float)`：在指定坐标添加指定名称的参考点。

- `remove_reference_point(reference_point_id: str)`：删除参考点。

- `launch_aircraft_from_airbase(airbase_id: str)`：从空军基地起飞一架飞机。

- `launch_aircraft_from_ship(ship_id: str)`：从舰船起飞一架飞机。

- `create_patrol_mission(mission_name: str, assigned_units: list[str], assigned_area: list[list[float]])`：创建巡逻任务。

- `update_patrol_mission(mission_id: str, mission_name: str, assigned_units: list[str], assigned_area: list[list[float]])`：使用新参数更新巡逻任务。

- `create_strike_mission(mission_name: str, assigned_attackers: list[str], assigned_targets: list[str])`：创建打击任务。

- `update_strike_mission(mission_id: str, mission_name: str, assigned_attackers: list[str], assigned_targets: list[str])`：使用新参数更新打击任务。

- `delete_mission(mission_id: str)`：删除任务。

- `move_aircraft(aircraft_id: str, new_coordinates: list)`：指挥飞机飞往航路点。

- `move_ship(ship_id: str, new_coordinates: list)`：指挥舰船驶往航路点。

- `handle_aircraft_attack(aircraft_id: str, target_id: str)`：从飞机向目标发射武器。

- `handle_ship_attack(ship_id: str, target_id: str)`：从舰船向目标发射武器。

- `aircraft_return_to_base(aircraft_id: str)`：指挥飞机返回其所属基地或最近的基地。

- `land_aircraft(aircraft_id: str)`：让飞机在其所属基地或最近的基地降落。
