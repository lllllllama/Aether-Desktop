"""
Aether Desktop - 工具模块
========================

这个包包含了 Aether Desktop 的所有底层工具和实用函数。

模块说明:
- icon_manager: Windows桌面图标交互管理器
- config_manager: 配置文件管理器  
- logger: 统一日志系统
- ai_providers: AI服务提供商管理器

作者: Aether Desktop Team
版本: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Aether Desktop Team"

# 导出主要类和函数
from .config_manager import ConfigManager
from .logger import setup_logger
from .ai_providers import ai_manager

__all__ = [
    "ConfigManager",
    "setup_logger",
    "ai_manager",
]
