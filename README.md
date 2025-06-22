# Aether Desktop - 智能桌面管家

## 🌟 项目概述

Aether Desktop 是一个基于AI的智能桌面管家应用，能够学习用户的桌面文件布局习惯，自动将新文件放置到最合适的位置，并支持自然语言指令进行高级整理。

## 🏗️ 核心架构

采用"云端大脑 + 本地助理"的混合架构：

- **云端大脑 (Cloud Brain):** 由大型语言模型（LLM）驱动，负责高层次的战略分析和规则生成
- **本地助理 (Local Assistant):** 轻量级Python脚本，负责实时文件监控和图标移动操作

## 📁 项目结构

```text
Aether_Desktop/
├── main.py                 # 程序入口，系统托盘UI
├── perception.py           # 感知层：桌面状态采集
├── strategy.py             # 认知层：AI大脑接口
├── execution.py            # 执行层：本地助理核心
├── utils/
│   ├── __init__.py
│   ├── icon_manager.py     # 桌面图标交互子系统
│   ├── config_manager.py   # 配置管理
│   └── logger.py          # 日志系统
├── data/
│   ├── rules.json          # AI生成的整理规则
│   ├── user_corrections.json  # 用户修正记录
│   └── desktop_regions.json   # 桌面区域定义
├── assets/
│   ├── icons/             # 应用图标资源
│   └── templates/         # Prompt模板
├── tests/                 # 单元测试
├── requirements.txt       # 依赖包列表
├── config.ini            # 配置文件
└── setup.py              # 安装脚本
```

## 🚀 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 配置API密钥：编辑 `config.ini`
3. 运行程序：`python main.py`

## 🔧 开发状态

- [x] 项目架构设计
- [ ] 底层图标管理器实现
- [ ] 桌面状态感知系统
- [ ] AI策略生成接口
- [ ] 文件监控执行引擎
- [ ] 系统托盘界面
- [ ] 用户配置管理

## 📄 许可证

MIT License
