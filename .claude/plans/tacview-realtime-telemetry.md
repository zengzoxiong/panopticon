# Tacview 实时遥测 - 异步双通道方案

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    Python 后端 (仿真引擎)                 │
│                                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │  仿真循环    │───▶│  TCP 输出   │───▶│ Tacview     │   │
│  │  (数据源)   │    │  (ACMI)     │    │ TCP:42674   │   │
│  └─────────────┘    └─────────────┘    └─────────────┘   │
│         │                                                │
│         │            ┌─────────────┐    ┌─────────────┐   │
│         └───────────▶│ WebSocket   │───▶│ React 前端  │   │
│                      │ (JSON)      │    │ WS:8765     │   │
│                      └─────────────┘    └─────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 核心特性

1. **原生 JSON 输出**：后端直接输出 JSON 格式，无需转换
2. **异步双通道**：TCP 和 WebSocket 独立运行，互不干涉
3. **同一数据源**：两种连接同时输出同一时刻的数据流
4. **零延迟**：数据产生后立即推送到两个通道

## 实现步骤

### 1. 修改后端 TCPStreamer

**文件**: `gym/blade/utils/TCPStreamer.py`

新增功能：
- 添加 WebSocket 服务器（端口 8765）
- 在 `stream_step()` 中同时输出两种格式
- TCP: ACMI 格式
- WebSocket: JSON 格式

### 2. 前端增加实时遥测模式

**新文件**:
- `src/game/realtime/RealtimeTelemetryPlayer.ts` - 实时遥测播放器类
- `src/gui/map/toolbar/RealtimeTelemetryPlayer.tsx` - 实时遥测播放器组件

**修改文件**:
- `src/gui/map/toolbar/Toolbar.tsx` - 添加实时遥测模式切换按钮
- `src/gui/map/ScenarioMap.tsx` - 集成实时遥测模式

### 3. 启动脚本

**文件**: `gym/scripts/simple_demo/demo_realtime_websocket.py`

功能：
- 启动 Python 仿真后端
- 同时启动 TCP:42674 和 WebSocket:8765
- 输出连接地址供前端和 Tacview 使用

## 数据格式

### WebSocket JSON 格式

```json
{
  "timestamp": 1234567890,
  "step": 100,
  "objects": [
    {
      "id": "fbcaa81c-bb50-470b-9e6d-81cd825b1fd0",
      "type": "Aircraft",
      "name": "F16",
      "color": "Blue",
      "longitude": 123.456,
      "latitude": 56.789,
      "altitude": 1000,
      "heading": 90,
      "speed": 250
    }
  ]
}
```

## 预期效果

- Tacview 通过 TCP:42674 接收 ACMI 数据
- 前端通过 WebSocket:8765 接收 JSON 数据
- 两种连接互不影响，可随时断开/重连
- 数据同步，延迟 < 10ms
