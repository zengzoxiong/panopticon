# BLADE 项目结构

项目分为两个目录：`client` 和 `gym`。

- `client` 包含 Web 应用程序的源代码。
- `gym` 包含 Gymnasium 环境的源代码。

截至本文撰写时，`client` 和 `gym` 都有各自独立的仿真引擎副本：

- Web 应用程序使用 TypeScript。
- Gymnasium 环境使用 Python。

未来，这两个实现将被整合。

## 仿真引擎

- Web 应用程序引擎：`client/src/game`
- Gymnasium 环境引擎：`gym/blade`

## Web 应用程序技术

我们使用 React 和 OpenLayers 构建 Web 应用程序。Web 应用程序源代码中的关键文件夹：

- `game`：仿真引擎（`gym` 也有 Python 版本）。
- `gui`：地图、工具栏和其他前端功能的代码。
- `scenarios`：包含 JSON 格式的示例场景文件。
- `styles`：包含 Web 应用程序的样式。
- `tests`：包含测试。
- `utils`：包含辅助函数和常量。

## GUI 文件夹结构

- `assets`：地图上使用的 SVG 图标文件。
- `map`：地图和工具栏的代码。
- `contextProviders`：鼠标位置、当前场景时间和仿真状态的提供者。
- `featureCards`：选中地图要素的弹出窗口（卡片）组件。
- `mapLayers`：地图图层，包括底图和要素图层（飞机、舰船、航线、距离环、标签等）。
- `missionEditor`：任务创建和编辑菜单。
- `toolbar`：工具栏的代码。
- `FeaturePopup.tsx`：地图要素弹出窗口的基础组件。
- `MultipleFeatureSelector.tsx`：处理多个要素的选择。
- `ScenarioMap.tsx`：渲染地图、图层和工具栏。
- `styles`：地图的样式。

## 引擎项目结构

- `db`：包含单位（飞机、基地、SAM 等）的真实/概念数据的"数据库"。
- `engine`：核心仿真逻辑（例如武器交战）。
- `envs`（仅在 `gym` 中）：Gymnasium 环境定义。
- `mission`：任务逻辑。
- `scenarios`（仅在 `gym` 中）：JSON 格式的示例场景。
- `units`：单位类别（例如飞机、舰船、基地）。
- `utils`（仅在 `gym` 中）：辅助函数和常量。
- `Game.*`：主仿真类。
- `Scenario.*`：场景类。
- `Side.*`：场景方类。
