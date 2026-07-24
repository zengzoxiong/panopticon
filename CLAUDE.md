# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

Panopticon 是一个基于 Web 的军事仿真平台，兼容 OpenAI Gym。项目由两个主要组件组成：

- **client/**：React + TypeScript 前端，使用 Vite 构建系统
- **gym/**：Python 包 (BLADE)，用于强化学习环境

## 开发命令

### 客户端（前端）

```bash
cd client

# 安装依赖
npm install

# 启动开发服务器（端口 3000）
npm run start
# 或
npm run dev

# 生产环境构建
npm run build

# 运行 lint 检查
npm run lint

# 代码格式化
npm run format

# 运行测试
npm test

# 监视模式运行测试
npm run test:watch

# 运行特定测试套件
npm run test:game      # 游戏逻辑测试
npm run test:units     # 单位测试
npm run test:utils     # 工具函数测试

# 结束进程
netstat -ano | findstr :3000    # 查找占用的端口
taskkill /PID {PID} /F          # 强制结束进程
```

### Gym（Python 后端）

```bash
cd gym

# 创建并激活Conda环境
conda create -n panopticon
conda activate panopticon

# 以可编辑模式安装
pip install -e .

# 安装包含 gym 依赖
pip install -e .[gym]

# 运行演示脚本
python scripts/simple_demo/demo.py

# 退出Conda环境
conda deactivate
```

## 架构

### 客户端架构

客户端是一个使用 TypeScript 和 Vite 的 React 应用：

**核心游戏逻辑** (`src/game/`)：
- `Game.ts`：主游戏控制器，管理仿真状态、时间压缩和单位交互
- `Scenario.ts`：想定配置和单位管理
- `Side.ts`：表示仿真中的军事阵营/方
- `Doctrine.ts`：军事条令和交战规则
- `Relationships.ts`：各方之间的外交关系

**单位类型** (`src/game/units/`)：
- `Aircraft.ts`：飞机单位，包含飞行动力学
- `Ship.ts`：海军舰艇
- `Airbase.ts`：军事空军基地
- `Facility.ts`：地面设施
- `Weapon.ts`：武器系统
- `ReferencePoint.ts`：地理参考点

**任务系统** (`src/game/mission/`)：
- `PatrolMission.ts`：巡逻路线管理
- `StrikeMission.ts`：打击任务协调

**战斗引擎** (`src/game/engine/`)：
- `weaponEngagement.ts`：武器交战逻辑、威胁检测和目标锁定

**GUI 层** (`src/gui/`)：
- `map/`：基于 OpenLayers 的地图可视化
- `mapLayers/`：地图图层管理（底图、要素、样式）

**数据库** (`src/game/db/`)：
- `UnitDb.ts`：单位数据库和查询
- `models/`：不同单位类型的数据模型

### Gym 架构

Gym 包提供兼容 OpenAI Gym 的环境：

**核心组件** (`blade/`)：
- `Game.py`：游戏逻辑的 Python 实现
- `Scenario.py`：想定管理
- `Side.py`：军事方表示
- `envs/blade.py`：Gymnasium 环境封装（`BLADE` 类）

**主要特性**：
- 使用 Gymnasium 的 Text 空间作为观测和动作空间
- 可配置的奖励、观测和终止过滤器
- 与 stable-baselines3 集成用于强化学习训练

### 数据流

1. 想定以 JSON 格式定义（参见 `client/src/scenarios/`）
2. `Scenario.ts` 加载并解析想定数据
3. `Game.ts` 管理仿真循环和单位更新
4. `weaponEngagement.ts` 处理战斗计算
5. GUI 组件在 OpenLayers 地图上渲染状态

## 测试

测试使用 Vitest 和 jsdom 环境：

- 测试文件：`*.spec.ts` 与源文件并置
- 设置文件：`src/testing/setup.ts`
- 辅助工具：`src/testing/helpers.ts`

## 代码风格

- 启用 TypeScript 严格模式
- 使用 ESLint + Prettier 进行格式化
- 路径别名：`@/` 映射到 `src/`

## 关键依赖

**客户端**：
- React 18 + TypeScript
- OpenLayers (ol) 用于地图可视化
- MUI (Material-UI) 用于 UI 组件
- Auth0 用于身份验证
- Vite 用于构建工具

**Gym**：
- Python 3.12.3
- Gymnasium 0.29.1
- stable-baselines3 2.4.1
- Shapely 用于几何运算

## 个人学习内容
1. 本项目不是前后端分离的项目，前端与后端均具备自身完整的仿真逻辑，均可独立运行。
2. 前端具备两种播放方式：根据想定文件（JSON）实时计算仿真、根据录像（JSONL）回放。后端可通过硬编码/强化学习的方式实现仿真。
3. 项目的完整工作流：前端设计想定 → 后端进行强化学习 → 生成录制文件 → 前端回放展示。

## 当前需要完成任务
- [x] 按照技术文档要求，安装本地依赖
- [x] 运行前后端，进行demo测试 
- [x] 前端增加language设置，允许切换语言（Language）：中文(Chinese)/英语(English)
- [x] 使用understandanything-skill理清代码依赖，找出代码运行逻辑，找出代码的主入口
- [x] 修改回放录制相关的gym\blade\utils\PlaybackRecorder.py，支持输出ACMI格式数据供Tacview回放使用
- [x] 增加实时播放相关的gym\blade\utils\TCPStreamer.py，支持通过TCP格式输出ACMI格式数据，在Tacview上进行实时遥测数据
- [ ] 修改实时播放相关的gym\blade\utils\TCPStreamer.py，支持通过TCP格式输出JSON格式数据，在client（前端）上进行实时遥测数据
- [ ] 修改client（前端）上增加实时遥测数据的模式