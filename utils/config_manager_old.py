"""
配置管理器 - Aether Desktop
===========================

负责管理应用程序的所有配置信息，包括AI配置、桌面设置、文件处理规则等。

主要功能:
1. 读取和解析配置文件
2. 提供类型安全的配置访问接口
3. 支持运行时配置更新
4. 配置验证和默认值处理

作者: Aether Desktop Team
版本: 1.0.0
"""

import os
import configparser
from typing import Dict, Any, Optional, Union
from pathlib import Path
from loguru import logger


class ConfigManager:
    """配置管理器类
    
    统一管理应用程序的所有配置信息，提供类型安全的访问接口。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = configparser.ConfigParser()
        self._load_config()
        
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        current_dir = Path(__file__).parent.parent
        return str(current_dir / "config.ini")
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                self.config.read(self.config_path, encoding='utf-8')
                logger.info(f"配置文件加载成功: {self.config_path}")
            else:
                logger.warning(f"配置文件不存在: {self.config_path}，将使用默认配置")
                self._create_default_config()        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            raise
    
    def _create_default_config(self) -> None:
        """创建默认配置文件"""
        # 这里可以添加默认配置创建逻辑
        logger.info("使用内置默认配置")
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """获取配置值
        
        Args:
            section: 配置段名
            key: 配置键名
            fallback: 默认值
            
        Returns:
            配置值或默认值
        """
        try:
            value = self.config.get(section, key, fallback=fallback)
            # 扩展环境变量
            if isinstance(value, str):
                value = os.path.expandvars(value)
            return value
        except (configparser.NoSectionError, configparser.NoOptionError):
            logger.warning(f"配置项不存在: [{section}] {key}，使用默认值: {fallback}")
            return fallback
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """获取整数配置值"""
        try:
            return self.config.getint(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            logger.warning(f"整数配置项获取失败: [{section}] {key}，使用默认值: {fallback}")
            return fallback
    
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """获取浮点数配置值"""
        try:
            return self.config.getfloat(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            logger.warning(f"浮点数配置项获取失败: [{section}] {key}，使用默认值: {fallback}")
            return fallback
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """获取布尔配置值"""
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            logger.warning(f"布尔配置项获取失败: [{section}] {key}，使用默认值: {fallback}")
            return fallback
    
    def get_list(self, section: str, key: str, separator: str = ',', fallback: list = None) -> list:
        """获取列表配置值
        
        Args:
            section: 配置段名
            key: 配置键名
            separator: 分隔符
            fallback: 默认值
            
        Returns:
            解析后的列表
        """
        if fallback is None:
            fallback = []
            
        try:
            value = self.config.get(section, key)
            if value:
                return [item.strip() for item in value.split(separator) if item.strip()]
            return fallback
        except (configparser.NoSectionError, configparser.NoOptionError):
            logger.warning(f"列表配置项获取失败: [{section}] {key}，使用默认值: {fallback}")
            return fallback
    
    def set(self, section: str, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            section: 配置段名
            key: 配置键名
            value: 配置值
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))
        logger.debug(f"配置项已更新: [{section}] {key} = {value}")
    
    def save(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            logger.info(f"配置已保存到: {self.config_path}")
        except Exception as e:
            logger.error(f"配置保存失败: {e}")
            raise
    
    def reload(self) -> None:
        """重新加载配置文件"""
        self._load_config()
        logger.info("配置文件已重新加载")
    
    # ==================== 便捷访问方法 ====================
    
    @property
    def ai_config(self) -> Dict[str, Any]:
        """获取AI配置"""
        return {
            'ai_provider': self.get('AI_CONFIG', 'ai_provider', 'gemini'),
            'gemini_api_key': self.get('AI_CONFIG', 'gemini_api_key', ''),
            'gemini_model': self.get('AI_CONFIG', 'gemini_model', 'gemini-1.5-pro'),
            'max_tokens': self.get_int('AI_CONFIG', 'max_tokens', 8192),
            'temperature': self.get_float('AI_CONFIG', 'temperature', 0.7),
            'use_function_calling': self.get_bool('AI_CONFIG', 'use_function_calling', True),
            'max_retry_attempts': self.get_int('AI_CONFIG', 'max_retry_attempts', 3),
        }
    
    @property
    def desktop_config(self) -> Dict[str, Any]:
        """获取桌面配置"""
        return {
            'monitor_desktop': self.get_bool('DESKTOP_CONFIG', 'monitor_desktop', True),
            'desktop_path': self.get('DESKTOP_CONFIG', 'desktop_path', os.path.expanduser('~/Desktop')),
            'scan_interval': self.get_float('DESKTOP_CONFIG', 'scan_interval', 2.0),
            'auto_organize': self.get_bool('DESKTOP_CONFIG', 'auto_organize', True),
            'region_grid_size': self.get_int('DESKTOP_CONFIG', 'region_grid_size', 4),
            'region_margin': self.get_int('DESKTOP_CONFIG', 'region_margin', 20),
        }
    
    @property
    def file_config(self) -> Dict[str, Any]:
        """获取文件配置"""
        return {
            'supported_extensions': self.get_list('FILE_CONFIG', 'supported_extensions'),
            'max_file_size_mb': self.get_int('FILE_CONFIG', 'max_file_size_mb', 500),
            'ignore_system_files': self.get_bool('FILE_CONFIG', 'ignore_system_files', True),
            'backup_before_move': self.get_bool('FILE_CONFIG', 'backup_before_move', False),
            'create_shortcuts': self.get_bool('FILE_CONFIG', 'create_shortcuts', False),
        }
    
    def validate_config(self) -> bool:
        """验证配置的有效性
        
        Returns:
            配置是否有效
        """
        is_valid = True
        
        # 检查AI配置
        ai_config = self.ai_config
        if not ai_config['gemini_api_key']:
            logger.warning("Gemini API密钥未配置")
            is_valid = False
        
        # 检查桌面路径
        desktop_config = self.desktop_config
        if not os.path.exists(desktop_config['desktop_path']):
            logger.warning(f"桌面路径不存在: {desktop_config['desktop_path']}")
            is_valid = False
        
        return is_valid


# 全局配置实例
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
