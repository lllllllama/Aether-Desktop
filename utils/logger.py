"""
日志系统 - Aether Desktop
========================

统一的日志管理系统，支持文件日志、控制台输出、日志轮转等功能。

主要功能:
1. 多级别日志记录 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
2. 文件日志轮转
3. 彩色控制台输出
4. 结构化日志格式
5. 性能监控日志

作者: Aether Desktop Team
版本: 1.0.0
"""

import os
import sys
from pathlib import Path
from typing import Optional
from loguru import logger


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: str = "10 MB",
    rotation_count: int = 5,
    enable_console: bool = True,
    log_format: Optional[str] = None
) -> None:
    """设置全局日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，None表示不写文件
        max_file_size: 单个日志文件最大大小
        rotation_count: 保留的日志文件数量
        enable_console: 是否启用控制台输出
        log_format: 自定义日志格式
    """
    
    # 移除默认处理器
    logger.remove()
    
    # 默认日志格式
    if log_format is None:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # 控制台输出处理器
    if enable_console:
        logger.add(
            sys.stderr,
            level=log_level,
            format=log_format,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    # 文件输出处理器
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            level=log_level,
            format=log_format,
            rotation=max_file_size,
            retention=rotation_count,
            compression="zip",
            backtrace=True,
            diagnose=True,
            encoding="utf-8"
        )
    
    logger.info("日志系统初始化完成")
    logger.debug(f"日志级别: {log_level}")
    logger.debug(f"日志文件: {log_file}")
    logger.debug(f"控制台输出: {enable_console}")


def get_logger(name: str = None):
    """获取指定名称的日志器
    
    Args:
        name: 日志器名称，通常使用 __name__
        
    Returns:
        配置好的日志器实例
    """
    if name:
        return logger.bind(name=name)
    return logger


class LoggerMixin:
    """日志混入类
    
    为其他类提供便捷的日志记录功能。
    """
    
    @property
    def logger(self):
        """获取当前类的日志器"""
        return get_logger(self.__class__.__name__)


def log_performance(func):
    """性能监控装饰器
    
    自动记录函数执行时间和性能信息。
    
    Usage:
        @log_performance
        def some_function():
            pass
    """
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func_logger = get_logger(f"{func.__module__}.{func.__name__}")
        
        try:
            func_logger.debug(f"开始执行: {func.__name__}")
            result = func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            func_logger.info(f"执行完成: {func.__name__} (耗时: {execution_time:.3f}秒)")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            func_logger.error(f"执行失败: {func.__name__} (耗时: {execution_time:.3f}秒) - {str(e)}")
            raise
    
    return wrapper


def log_exception(func):
    """异常记录装饰器
    
    自动记录函数中的异常信息。
    
    Usage:
        @log_exception
        def some_function():
            pass
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_logger = get_logger(f"{func.__module__}.{func.__name__}")
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            func_logger.exception(f"函数 {func.__name__} 发生异常: {str(e)}")
            raise
    
    return wrapper


# 便捷的日志记录函数
def debug(message: str, **kwargs):
    """记录调试信息"""
    logger.debug(message, **kwargs)


def info(message: str, **kwargs):
    """记录一般信息"""
    logger.info(message, **kwargs)


def warning(message: str, **kwargs):
    """记录警告信息"""
    logger.warning(message, **kwargs)


def error(message: str, **kwargs):
    """记录错误信息"""
    logger.error(message, **kwargs)


def critical(message: str, **kwargs):
    """记录严重错误信息"""
    logger.critical(message, **kwargs)


def exception(message: str, **kwargs):
    """记录异常信息（包含堆栈跟踪）"""
    logger.exception(message, **kwargs)


# 初始化默认日志配置
def init_default_logger():
    """初始化默认日志配置"""
    try:
        from .config_manager import get_config
        config = get_config()
        
        # 从配置文件读取日志设置
        log_level = config.get('LOGGING_CONFIG', 'log_level', 'INFO')
        log_file = config.get('LOGGING_CONFIG', 'log_file', 'logs/aether_desktop.log')
        max_log_size = config.get('LOGGING_CONFIG', 'max_log_size_mb', '10')
        rotation_count = config.get_int('LOGGING_CONFIG', 'log_rotation_count', 5)
        enable_console = config.get_bool('LOGGING_CONFIG', 'enable_console_output', True)
        
        # 设置日志系统
        setup_logger(
            log_level=log_level,
            log_file=log_file,
            max_file_size=f"{max_log_size} MB",
            rotation_count=rotation_count,
            enable_console=enable_console
        )
        
    except Exception as e:
        # 如果配置加载失败，使用默认设置
        setup_logger(
            log_level="INFO",
            log_file="logs/aether_desktop.log",
            enable_console=True
        )
        logger.warning(f"使用默认日志配置，配置加载失败: {e}")


# 模块加载时自动初始化
if __name__ != "__main__":
    init_default_logger()
