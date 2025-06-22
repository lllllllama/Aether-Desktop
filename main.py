"""
主程序入口 - Aether Desktop
==========================

Aether Desktop 智能桌面管家的主程序入口。
提供系统托盘界面，协调各个模块的工作。

核心功能:
1. 系统托盘界面和菜单
2. 模块间协调和通信
3. 应用生命周期管理
4. 用户交互处理
5. 错误监控和恢复

技术特点:
- 优雅的后台服务设计
- 直观的用户界面
- 健壮的错误处理
- 资源自动清理

作者: Aether Desktop Team
版本: 1.0.0
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    print("错误: 需要安装 pystray 和 Pillow 库")
    print("请运行: pip install pystray Pillow")
    sys.exit(1)

from utils.logger import setup_logger, get_logger, log_exception
from utils.config_manager import get_config
from perception import get_perception, create_snapshot
from strategy import get_strategy_engine, generate_smart_rules
from execution import get_execution_engine, start_desktop_monitoring, stop_desktop_monitoring, organize_desktop_now


class AetherDesktopApp:
    """Aether Desktop 主应用程序类"""
    
    def __init__(self):
        """初始化应用程序"""
        # 初始化日志系统
        self._setup_logging()
        
        self.logger = get_logger(self.__class__.__name__)
        self.config = get_config()
        
        # 应用状态
        self.is_running = False
        self.monitoring_active = False
        self.last_organize_time = None
        
        # 模块实例
        self.perception = None
        self.strategy_engine = None
        self.execution_engine = None
        
        # 系统托盘
        self.tray_icon = None
        self.icon_image = None
        
        self.logger.info("=== Aether Desktop 启动 ===")
        self.logger.info(f"版本: 1.0.0")
        self.logger.info(f"Python: {sys.version}")
        
    def _setup_logging(self):
        """设置日志系统"""
        try:
            # 从配置文件读取日志设置，如果失败则使用默认设置
            try:
                config = get_config()
                log_level = config.get('LOGGING_CONFIG', 'log_level', 'INFO')
                log_file = config.get('LOGGING_CONFIG', 'log_file', 'logs/aether_desktop.log')
                enable_console = config.get_bool('LOGGING_CONFIG', 'enable_console_output', True)
            except:
                log_level = 'INFO'
                log_file = 'logs/aether_desktop.log'
                enable_console = True
            
            setup_logger(
                log_level=log_level,
                log_file=log_file,
                enable_console=enable_console
            )
            
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            # 使用最基本的日志设置
            setup_logger(log_level='INFO', enable_console=True)
    
    def initialize_modules(self) -> bool:
        """初始化所有模块"""
        try:
            self.logger.info("正在初始化核心模块...")
            
            # 验证配置
            if not self.config.validate_config():
                self.logger.error("配置验证失败")
                return False
            
            # 初始化感知系统
            self.perception = get_perception()
            self.logger.debug("感知系统初始化完成")
            
            # 初始化策略引擎
            try:
                self.strategy_engine = get_strategy_engine()
                self.logger.debug("AI策略引擎初始化完成")
            except Exception as e:
                self.logger.warning(f"AI策略引擎初始化失败: {e}")
                self.logger.warning("将在没有AI功能的情况下运行")
                self.strategy_engine = None
            
            # 初始化执行引擎
            self.execution_engine = get_execution_engine()
            self.logger.debug("执行引擎初始化完成")
            
            self.logger.info("所有模块初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"模块初始化失败: {e}")
            return False
    
    def create_tray_icon(self) -> None:
        """创建系统托盘图标"""
        try:
            # 创建图标图像
            self.icon_image = self._create_icon_image()
            
            # 创建托盘菜单
            menu = pystray.Menu(
                pystray.MenuItem("Aether Desktop", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "立即优化桌面", 
                    self._on_organize_now,
                    enabled=True
                ),
                pystray.MenuItem(
                    "开启自动整理" if not self.monitoring_active else "停止自动整理",
                    self._on_toggle_monitoring,
                    enabled=True
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("生成AI规则", self._on_generate_rules, enabled=self.strategy_engine is not None),
                pystray.MenuItem("查看统计信息", self._on_show_stats),
                pystray.MenuItem("打开桌面目录", self._on_open_desktop),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("关于", self._on_about),
                pystray.MenuItem("退出", self._on_quit)
            )
            
            # 创建托盘图标
            self.tray_icon = pystray.Icon(
                "aether_desktop",
                self.icon_image,
                "Aether Desktop - 智能桌面管家",
                menu
            )
            
            self.logger.debug("系统托盘图标创建完成")
            
        except Exception as e:
            self.logger.error(f"创建托盘图标失败: {e}")
            raise
    
    def _create_icon_image(self) -> Image.Image:
        """创建托盘图标图像"""
        try:
            # 检查是否有自定义图标
            icon_path = Path(__file__).parent / "assets" / "icons" / "tray_icon.png"
            
            if icon_path.exists():
                return Image.open(icon_path)
            else:
                # 创建简单的默认图标
                size = 64
                image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(image)
                
                # 绘制简单的桌面图标
                margin = 8
                draw.rectangle(
                    [margin, margin, size-margin, size-margin],
                    fill=(70, 130, 180, 255),  # 钢蓝色
                    outline=(25, 25, 112, 255)  # 深蓝色边框
                )
                
                # 绘制一些小方块代表文件
                for i in range(3):
                    for j in range(3):
                        x = margin + 10 + j * 12
                        y = margin + 10 + i * 12
                        draw.rectangle(
                            [x, y, x+8, y+8],
                            fill=(255, 255, 255, 200)
                        )
                
                return image
                
        except Exception as e:
            self.logger.warning(f"创建图标图像失败: {e}")
            # 返回最简单的图标
            image = Image.new('RGBA', (16, 16), (70, 130, 180, 255))
            return image
    
    def run(self) -> None:
        """运行应用程序"""
        try:
            self.logger.info("Aether Desktop 正在启动...")
            
            # 初始化模块
            if not self.initialize_modules():
                self.logger.error("模块初始化失败，程序退出")
                return
            
            # 创建托盘图标
            self.create_tray_icon()
            
            # 设置应用状态
            self.is_running = True
            
            # 自动启动监控（如果配置了的话）
            if self.config.desktop_config.get('auto_organize', False):
                self._start_monitoring()
            
            self.logger.info("Aether Desktop 启动完成，运行在系统托盘")
            
            # 运行托盘图标（阻塞主线程）
            self.tray_icon.run()
            
        except KeyboardInterrupt:
            self.logger.info("收到键盘中断信号")
            self.shutdown()
        except Exception as e:
            self.logger.error(f"应用程序运行失败: {e}")
            self.shutdown()
    
    # ==================== 托盘菜单事件处理 ====================
    
    def _on_organize_now(self, icon, item):
        """立即整理桌面"""
        try:
            self.logger.info("用户请求立即整理桌面")
            
            def organize_task():
                try:
                    # 显示通知
                    if hasattr(self.tray_icon, 'notify'):
                        self.tray_icon.notify("正在整理桌面...", "Aether Desktop")
                    
                    # 执行整理
                    results = organize_desktop_now()
                    
                    # 显示结果
                    if 'error' not in results:
                        message = f"整理完成！成功: {results['organized_files']}, 失败: {results['failed_files']}"
                        self.logger.info(message)
                        
                        if hasattr(self.tray_icon, 'notify'):
                            self.tray_icon.notify(message, "Aether Desktop")
                    else:
                        error_msg = f"整理失败: {results['error']}"
                        self.logger.error(error_msg)
                        
                        if hasattr(self.tray_icon, 'notify'):
                            self.tray_icon.notify(error_msg, "Aether Desktop")
                    
                    self.last_organize_time = datetime.now()
                    
                except Exception as e:
                    self.logger.error(f"整理桌面失败: {e}")
            
            # 在后台线程执行
            threading.Thread(target=organize_task, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"处理整理请求失败: {e}")
    
    def _on_toggle_monitoring(self, icon, item):
        """切换监控状态"""
        try:
            if self.monitoring_active:
                self._stop_monitoring()
            else:
                self._start_monitoring()
            
            # 更新菜单
            self._update_menu()
            
        except Exception as e:
            self.logger.error(f"切换监控状态失败: {e}")
    
    def _start_monitoring(self):
        """启动监控"""
        try:
            if start_desktop_monitoring():
                self.monitoring_active = True
                self.logger.info("桌面监控已启动")
                
                if hasattr(self.tray_icon, 'notify'):
                    self.tray_icon.notify("自动整理已开启", "Aether Desktop")
            else:
                self.logger.error("启动桌面监控失败")
                
        except Exception as e:
            self.logger.error(f"启动监控失败: {e}")
    
    def _stop_monitoring(self):
        """停止监控"""
        try:
            stop_desktop_monitoring()
            self.monitoring_active = False
            self.logger.info("桌面监控已停止")
            
            if hasattr(self.tray_icon, 'notify'):
                self.tray_icon.notify("自动整理已停止", "Aether Desktop")
                
        except Exception as e:
            self.logger.error(f"停止监控失败: {e}")
    
    def _on_generate_rules(self, icon, item):
        """生成AI规则"""
        try:
            if not self.strategy_engine:
                self.logger.warning("AI策略引擎未初始化")
                return
            
            self.logger.info("用户请求生成AI规则")
            
            def generate_task():
                try:
                    if hasattr(self.tray_icon, 'notify'):
                        self.tray_icon.notify("正在生成AI规则...", "Aether Desktop")
                    
                    # 创建桌面快照
                    snapshot = create_snapshot()
                    
                    # 加载用户修正
                    corrections = self.perception.load_user_corrections()
                    
                    # 生成规则
                    ruleset = generate_smart_rules(snapshot, corrections)
                    
                    if ruleset:
                        # 保存规则
                        filepath = self.strategy_engine.save_rules_to_file(ruleset)
                        
                        # 加载到执行引擎
                        self.execution_engine.load_rules(ruleset)
                        
                        message = f"AI规则生成成功！共 {len(ruleset.rules)} 条规则"
                        self.logger.info(message)
                        
                        if hasattr(self.tray_icon, 'notify'):
                            self.tray_icon.notify(message, "Aether Desktop")
                    else:
                        error_msg = "AI规则生成失败"
                        self.logger.error(error_msg)
                        
                        if hasattr(self.tray_icon, 'notify'):
                            self.tray_icon.notify(error_msg, "Aether Desktop")
                    
                except Exception as e:
                    self.logger.error(f"生成AI规则失败: {e}")
            
            # 在后台线程执行
            threading.Thread(target=generate_task, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"处理AI规则生成请求失败: {e}")
    
    def _on_show_stats(self, icon, item):
        """显示统计信息"""
        try:
            stats = self.execution_engine.get_statistics()
            
            message = (
                f"运行时间: {stats.get('runtime_hours', 0):.1f} 小时\\n"
                f"处理文件: {stats.get('processed_files', 0)} 个\\n"
                f"成功移动: {stats.get('successful_moves', 0)} 个\\n"
                f"成功率: {stats.get('success_rate', 0):.1f}%\\n"
                f"监控状态: {'活跃' if stats.get('monitoring_active', False) else '停止'}"
            )
            
            self.logger.info(f"统计信息: {stats}")
            
            if hasattr(self.tray_icon, 'notify'):
                self.tray_icon.notify(message, "Aether Desktop 统计信息")
            
        except Exception as e:
            self.logger.error(f"显示统计信息失败: {e}")
    
    def _on_open_desktop(self, icon, item):
        """打开桌面目录"""
        try:
            desktop_path = self.config.desktop_config['desktop_path']
            
            if sys.platform == 'win32':
                os.startfile(desktop_path)
            elif sys.platform == 'darwin':
                os.system(f'open "{desktop_path}"')
            else:
                os.system(f'xdg-open "{desktop_path}"')
            
            self.logger.debug(f"打开桌面目录: {desktop_path}")
            
        except Exception as e:
            self.logger.error(f"打开桌面目录失败: {e}")
    
    def _on_about(self, icon, item):
        """显示关于信息"""
        try:
            message = (
                "Aether Desktop v1.0.0\\n"
                "智能桌面管家\\n\\n"
                "基于AI的桌面文件自动整理工具\\n"
                "让您的桌面保持整洁有序"
            )
            
            if hasattr(self.tray_icon, 'notify'):
                self.tray_icon.notify(message, "关于 Aether Desktop")
            
        except Exception as e:
            self.logger.error(f"显示关于信息失败: {e}")
    
    def _on_quit(self, icon, item):
        """退出应用程序"""
        self.logger.info("用户请求退出应用程序")
        self.shutdown()
    
    def _update_menu(self):
        """更新托盘菜单"""
        try:
            # 重新创建菜单
            menu = pystray.Menu(
                pystray.MenuItem("Aether Desktop", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("立即优化桌面", self._on_organize_now, enabled=True),
                pystray.MenuItem(
                    "停止自动整理" if self.monitoring_active else "开启自动整理",
                    self._on_toggle_monitoring,
                    enabled=True
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("生成AI规则", self._on_generate_rules, enabled=self.strategy_engine is not None),
                pystray.MenuItem("查看统计信息", self._on_show_stats),
                pystray.MenuItem("打开桌面目录", self._on_open_desktop),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("关于", self._on_about),
                pystray.MenuItem("退出", self._on_quit)
            )
            
            self.tray_icon.menu = menu
            
        except Exception as e:
            self.logger.error(f"更新菜单失败: {e}")
    
    @log_exception
    def shutdown(self):
        """关闭应用程序"""
        try:
            self.logger.info("正在关闭 Aether Desktop...")
            
            self.is_running = False
            
            # 停止监控
            if self.monitoring_active:
                self._stop_monitoring()
            
            # 清理资源
            if self.execution_engine:
                self.execution_engine.stop_monitoring()
            
            # 停止托盘图标
            if self.tray_icon:
                self.tray_icon.stop()
            
            self.logger.info("Aether Desktop 已安全关闭")
            
        except Exception as e:
            self.logger.error(f"关闭应用程序失败: {e}")


def main():
    """主函数"""
    try:
        # 检查是否已经在运行
        if sys.platform == 'win32':
            import win32event
            import win32api
            
            mutex = win32event.CreateMutex(None, False, 'AetherDesktopMutex')
            if win32api.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
                print("Aether Desktop 已经在运行")
                sys.exit(1)
        
        # 创建并运行应用程序
        app = AetherDesktopApp()
        app.run()
        
    except KeyboardInterrupt:
        print("\\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
