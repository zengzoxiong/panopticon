# 发现与决策

## 需求
- 为前端添加语言切换功能
- 支持中文和英文两种语言
- 生成中英翻译对照表供用户审核

## 研究发现
- 项目使用 React + TypeScript + Vite
- 现有代码中有大量硬编码的英文文本
- 需要使用国际化库来管理翻译
- 主要文本分布在以下组件中：
  - Toolbar.tsx：菜单、按钮、工具提示
  - AircraftCard.tsx：飞机属性标签
  - ShipCard.tsx：舰船属性标签
  - FacilityCard.tsx：设施属性标签
  - MissionCreatorCard.tsx：任务创建表单
  - SimulationLogs.tsx：日志过滤器
  - Login.tsx/Logout.tsx：认证相关文本

## 技术决策
| 决策 | 理由 |
|------|------|
| 使用 react-i18next | React 生态成熟的国际化解决方案，支持动态加载 |
| 使用 i18next | 底层库，功能强大，社区活跃 |
| 语言切换状态持久化 | 使用 localStorage 保存用户语言偏好 |

## 遇到的问题
| 问题 | 解决方案 |
|------|---------|
|      |         |

## 资源
- react-i18next 文档：https://react.i18next.com/
- i18next 文档：https://www.i18next.com/

## 视觉/浏览器发现
<!-- 关键：每执行2次查看/浏览器操作后更新此部分 -->
<!-- 多模态内容必须立即以文本形式记录 -->
-

---
*每执行2次查看/浏览器/搜索操作后更新此文件*
*防止视觉信息丢失*
