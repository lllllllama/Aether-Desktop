"""
执行层 - Aether Desktop
=====================

本地助理核心模块，负责实时监控桌面变化并执行AI生成的整理规则。
这是项目的"行动大脑"，将策略转化为具体的图标移动操作。

核心功能:
1. 实时文件系统监控（基于watchdog）
2. 智能规则匹配引擎
3. 无碰撞图标放置算法
4. 批量图标整理操作
5. 用户反馈收集

技术特点:
- 高效的事件驱动架构
- 智能防抖动机制
- 安全的并发控制
- 优雅的错误恢复

作者: Aether Desktop Team
版本: 1.0.0
"""

import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict, deque

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent
except ImportError:
    print("错误: 需要安装 watchdog 库")
    print("请运行: pip install watchdog")
    exit(1)

from utils.logger import get_logger, log_performance, log_exception
from utils.config_manager import get_config
from utils.icon_manager import get_icon_manager, DesktopRegion
from strategy import DesktopRuleset, IconPlacementRule


@dataclass
class PendingOperation:
    """待处理的操作"""
    filepath: str
    operation_type: str  # 'created', 'moved', 'organize'
    timestamp: datetime
    retries: int = 0
    max_retries: int = 3


class DesktopFileHandler(FileSystemEventHandler):
    """桌面文件事件处理器"""
    
    def __init__(self, execution_engine):
        """初始化文件处理器"""
        super().__init__()
        self.execution_engine = execution_engine
        self.logger = get_logger(self.__class__.__name__)
        
        # 防抖动配置
        self.debounce_delay = 2.0  # 秒
        self.pending_events = {}  # 文件路径 -> 最后事件时间
        
    def on_created(self, event):
        """文件创建事件处理"""
        if event.is_directory:
            return
        
        try:
            filepath = event.src_path
            self.logger.debug(f"检测到新文件: {filepath}")
            
            # 添加防抖动
            self._debounce_event(filepath, 'created')
            
        except Exception as e:
            self.logger.error(f"处理文件创建事件失败: {e}")
    
    def on_moved(self, event):
        """文件移动事件处理"""
        if event.is_directory:
            return
        
        try:
            dest_path = event.dest_path
            self.logger.debug(f"检测到文件移动: {dest_path}")
            
            # 添加防抖动
            self._debounce_event(dest_path, 'moved')
            
        except Exception as e:
            self.logger.error(f"处理文件移动事件失败: {e}")
    
    def _debounce_event(self, filepath: str, event_type: str):
        """防抖动处理"""
        current_time = datetime.now()
        self.pending_events[filepath] = {
            'time': current_time,
            'type': event_type
        }
        
        # 延迟处理
        def delayed_process():
            time.sleep(self.debounce_delay)
            
            # 检查是否还是最新事件
            if (filepath in self.pending_events and 
                self.pending_events[filepath]['time'] == current_time):
                
                # 处理事件
                self.execution_engine.add_pending_operation(
                    PendingOperation(
                        filepath=filepath,
                        operation_type=event_type,
                        timestamp=current_time
                    )
                )
                
                # 清理记录
                if filepath in self.pending_events:
                    del self.pending_events[filepath]
        
        # 在新线程中延迟处理
        threading.Thread(target=delayed_process, daemon=True).start()


class RuleEngine:
    """规则匹配引擎"""
    
    def __init__(self):
        """初始化规则引擎"""
        self.logger = get_logger(self.__class__.__name__)
        self.current_rules: Optional[DesktopRuleset] = None
        self.rule_cache = {}  # 文件路径 -> 匹配的规则
        
    def load_rules(self, ruleset: DesktopRuleset) -> None:
        """加载规则集"""
        try:
            self.current_rules = ruleset
            self.rule_cache.clear()  # 清理缓存
            
            self.logger.info(f"规则集已加载: {len(ruleset.rules)} 条规则")
            
            # 按优先级排序规则
            self.current_rules.rules.sort(key=lambda r: r.priority, reverse=True)
            
        except Exception as e:
            self.logger.error(f"加载规则失败: {e}")
    
    def find_matching_rule(self, filepath: str) -> Optional[IconPlacementRule]:
        """查找匹配的规则"""
        try:
            if not self.current_rules or not self.current_rules.rules:
                return None
            
            # 检查缓存
            if filepath in self.rule_cache:
                return self.rule_cache[filepath]
            
            # 获取文件信息
            file_info = self._analyze_file(filepath)
            if not file_info:
                return None
            
            # 遍历规则查找匹配
            for rule in self.current_rules.rules:
                if not rule.enabled:
                    continue
                
                if self._rule_matches_file(rule, file_info):
                    self.logger.debug(f"文件 {os.path.basename(filepath)} 匹配规则: {rule.name}")
                    self.rule_cache[filepath] = rule
                    return rule
            
            self.logger.debug(f"文件 {os.path.basename(filepath)} 无匹配规则")
            return None
            
        except Exception as e:
            self.logger.error(f"规则匹配失败: {e}")
            return None
    
    def _analyze_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """分析文件属性"""
        try:
            if not os.path.exists(filepath):
                return None
            
            stat = os.stat(filepath)
            filename = os.path.basename(filepath)
            name, ext = os.path.splitext(filename)
            
            # 文件类型映射
            type_mapping = {
                '.txt': 'document', '.doc': 'document', '.docx': 'document', '.pdf': 'document',
                '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image',
                '.mp4': 'video', '.avi': 'video', '.mkv': 'video',
                '.mp3': 'audio', '.wav': 'audio',
                '.zip': 'archive', '.rar': 'archive', '.7z': 'archive',
                '.exe': 'executable', '.msi': 'executable',
                '.lnk': 'shortcut'
            }
            
            file_type = type_mapping.get(ext.lower(), 'other')
            size_mb = stat.st_size / (1024 * 1024)
            
            # 大小分类
            if size_mb < 1:
                size_range = 'tiny'
            elif size_mb < 10:
                size_range = 'small'
            elif size_mb < 100:
                size_range = 'medium'
            elif size_mb < 1000:
                size_range = 'large'
            else:
                size_range = 'huge'
            
            return {
                'filename': filename,
                'name': name,
                'extension': ext.lower(),
                'file_type': file_type,
                'size_mb': size_mb,
                'size_range': size_range,
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'keywords': self._extract_keywords(filename.lower())
            }
            
        except Exception as e:
            self.logger.warning(f"分析文件失败 {filepath}: {e}")
            return None
    
    def _extract_keywords(self, filename: str) -> List[str]:
        """从文件名提取关键词"""
        # 简单的关键词提取
        common_keywords = {
            '工作': ['work', 'job', '工作', '项目', 'project'],
            '学习': ['study', 'learn', '学习', '课程', 'course'],
            '娱乐': ['game', 'movie', 'music', '游戏', '电影', '音乐'],
            '工具': ['tool', 'app', 'software', '工具', '软件'],
            '文档': ['doc', 'text', 'pdf', '文档', '资料']
        }
        
        found_keywords = []
        for category, words in common_keywords.items():
            for word in words:
                if word in filename:
                    found_keywords.append(category)
                    break
        
        return found_keywords
    
    def _rule_matches_file(self, rule: IconPlacementRule, file_info: Dict[str, Any]) -> bool:
        """检查规则是否匹配文件"""
        try:
            conditions = rule.conditions
            
            # 检查文件类型
            if 'file_type' in conditions:
                allowed_types = conditions['file_type']
                if isinstance(allowed_types, str):
                    allowed_types = [allowed_types]
                if file_info['file_type'] not in allowed_types:
                    return False
            
            # 检查文件扩展名
            if 'extensions' in conditions:
                allowed_exts = conditions['extensions']
                if isinstance(allowed_exts, str):
                    allowed_exts = [allowed_exts]
                if file_info['extension'] not in allowed_exts:
                    return False
            
            # 检查大小范围
            if 'size_range' in conditions:
                allowed_sizes = conditions['size_range']
                if isinstance(allowed_sizes, str):
                    allowed_sizes = [allowed_sizes]
                if file_info['size_range'] not in allowed_sizes:
                    return False
            
            # 检查关键词
            if 'keywords' in conditions:
                required_keywords = conditions['keywords']
                if isinstance(required_keywords, str):
                    required_keywords = [required_keywords]
                
                # 检查文件名或提取的关键词中是否包含要求的关键词
                filename_lower = file_info['filename'].lower()
                file_keywords = file_info.get('keywords', [])
                
                keyword_matched = False
                for keyword in required_keywords:
                    if keyword.lower() in filename_lower or keyword in file_keywords:
                        keyword_matched = True
                        break
                
                if not keyword_matched:
                    return False
            
            # 检查文件名模式
            if 'name_patterns' in conditions:
                patterns = conditions['name_patterns']
                if isinstance(patterns, str):
                    patterns = [patterns]
                
                pattern_matched = False
                for pattern in patterns:
                    if pattern.lower() in file_info['filename'].lower():
                        pattern_matched = True
                        break
                
                if not pattern_matched:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"规则匹配检查失败: {e}")
            return False


class PlacementEngine:
    """图标放置引擎"""
    
    def __init__(self):
        """初始化放置引擎"""
        self.logger = get_logger(self.__class__.__name__)
        self.icon_manager = get_icon_manager()
        self.occupied_positions = set()  # 已占用的位置
        self.placement_lock = threading.Lock()  # 放置操作锁
        
    def place_icon_in_region(self, filename: str, region_id: str) -> bool:
        """在指定区域放置图标"""
        try:
            with self.placement_lock:
                # 获取目标区域
                regions = self.icon_manager.get_desktop_regions()
                target_region = None
                
                for region in regions:
                    if region.id == region_id:
                        target_region = region
                        break
                
                if not target_region:
                    self.logger.error(f"未找到区域: {region_id}")
                    return False
                
                # 查找可用位置
                position = self._find_available_position(target_region)
                if not position:
                    self.logger.warning(f"区域 {region_id} 无可用位置")
                    return False
                
                x, y = position
                
                # 移动图标
                success = self.icon_manager.set_icon_position(filename, x, y)
                
                if success:
                    # 标记位置为已占用
                    self.occupied_positions.add((x, y))
                    self.logger.info(f"图标 {filename} 已放置到区域 {region_id} 位置 ({x}, {y})")
                
                return success
                
        except Exception as e:
            self.logger.error(f"放置图标失败: {e}")
            return False
    
    def _find_available_position(self, region: DesktopRegion) -> Optional[tuple]:
        """在区域内查找可用位置"""
        try:
            # 更新已占用位置
            self._update_occupied_positions()
            
            # 计算网格参数
            icon_size = region.grid_size
            margin = region.margin
            
            # 计算网格坐标
            start_x = region.x + margin
            start_y = region.y + margin
            
            max_x = region.x + region.width - icon_size - margin
            max_y = region.y + region.height - icon_size - margin
            
            # 按行列扫描查找空位
            y = start_y
            while y <= max_y:
                x = start_x
                while x <= max_x:
                    if (x, y) not in self.occupied_positions:
                        return (x, y)
                    x += icon_size + margin
                y += icon_size + margin
            
            return None
            
        except Exception as e:
            self.logger.error(f"查找可用位置失败: {e}")
            return None
    
    def _update_occupied_positions(self) -> None:
        """更新已占用位置信息"""
        try:
            # 获取当前所有图标位置
            icons = self.icon_manager.get_all_icon_positions()
            
            # 清空并重新填充
            self.occupied_positions.clear()
            
            for filename, icon_info in icons.items():
                self.occupied_positions.add((icon_info.x, icon_info.y))
            
        except Exception as e:
            self.logger.warning(f"更新占用位置失败: {e}")


class ExecutionEngine:
    """执行引擎主类"""
    
    def __init__(self):
        """初始化执行引擎"""
        self.logger = get_logger(self.__class__.__name__)
        self.config = get_config()
        
        # 子模块
        self.rule_engine = RuleEngine()
        self.placement_engine = PlacementEngine()
        
        # 监控配置
        self.desktop_path = self.config.desktop_config['desktop_path']
        self.auto_organize = self.config.desktop_config['auto_organize']
        
        # 文件监控
        self.observer = None
        self.file_handler = DesktopFileHandler(self)
        
        # 操作队列
        self.pending_operations = deque()
        self.processing_lock = threading.Lock()
        self.processing_thread = None
        self.stop_event = threading.Event()
        
        # 统计信息
        self.stats = {
            'processed_files': 0,
            'successful_moves': 0,
            'failed_moves': 0,
            'start_time': datetime.now()
        }
        
        self.logger.info("执行引擎初始化完成")
    
    @log_performance
    def start_monitoring(self) -> bool:
        """开始监控桌面"""
        try:
            if self.observer and self.observer.is_alive():
                self.logger.warning("桌面监控已在运行")
                return True
            
            # 创建观察者
            self.observer = Observer()
            self.observer.schedule(
                self.file_handler,
                self.desktop_path,
                recursive=False
            )
            
            # 启动监控
            self.observer.start()
            
            # 启动处理线程
            self.stop_event.clear()
            self.processing_thread = threading.Thread(
                target=self._process_operations,
                daemon=True
            )
            self.processing_thread.start()
            
            self.logger.info(f"桌面监控已启动: {self.desktop_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"启动桌面监控失败: {e}")
            return False
    
    def stop_monitoring(self) -> None:
        """停止监控桌面"""
        try:
            # 停止处理线程
            self.stop_event.set()
            
            # 停止文件观察者
            if self.observer and self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=5)
            
            # 等待处理线程结束
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)
            
            self.logger.info("桌面监控已停止")
            
        except Exception as e:
            self.logger.error(f"停止桌面监控失败: {e}")
    
    def load_rules(self, ruleset: DesktopRuleset) -> None:
        """加载整理规则"""
        self.rule_engine.load_rules(ruleset)
    
    def add_pending_operation(self, operation: PendingOperation) -> None:
        """添加待处理操作"""
        try:
            with self.processing_lock:
                self.pending_operations.append(operation)
            
            self.logger.debug(f"添加待处理操作: {operation.operation_type} - {os.path.basename(operation.filepath)}")
            
        except Exception as e:
            self.logger.error(f"添加待处理操作失败: {e}")
    
    def _process_operations(self) -> None:
        """处理操作队列（后台线程）"""
        self.logger.info("操作处理线程已启动")
        
        while not self.stop_event.is_set():
            try:
                # 检查是否有待处理操作
                operation = None
                with self.processing_lock:
                    if self.pending_operations:
                        operation = self.pending_operations.popleft()
                
                if operation:
                    self._execute_operation(operation)
                else:
                    # 没有操作时短暂休眠
                    time.sleep(0.5)
                    
            except Exception as e:
                self.logger.error(f"处理操作失败: {e}")
                time.sleep(1)
        
        self.logger.info("操作处理线程已停止")
    
    def _execute_operation(self, operation: PendingOperation) -> None:
        """执行单个操作"""
        try:
            self.stats['processed_files'] += 1
            
            # 检查自动整理是否启用
            if not self.auto_organize:
                return
            
            # 检查文件是否仍然存在
            if not os.path.exists(operation.filepath):
                self.logger.debug(f"文件不存在，跳过: {operation.filepath}")
                return
            
            # 查找匹配的规则
            rule = self.rule_engine.find_matching_rule(operation.filepath)
            if not rule:
                self.logger.debug(f"无匹配规则: {os.path.basename(operation.filepath)}")
                return
            
            # 执行图标放置
            filename = os.path.basename(operation.filepath)
            success = self.placement_engine.place_icon_in_region(filename, rule.target_region)
            
            if success:
                self.stats['successful_moves'] += 1
                self.logger.info(f"成功整理文件: {filename} -> {rule.target_region}")
            else:
                self.stats['failed_moves'] += 1
                
                # 重试机制
                if operation.retries < operation.max_retries:
                    operation.retries += 1
                    operation.timestamp = datetime.now()
                    
                    # 延迟重试
                    time.sleep(2 ** operation.retries)
                    self.add_pending_operation(operation)
                    
                    self.logger.warning(f"整理失败，将重试: {filename} (尝试 {operation.retries}/{operation.max_retries})")
                else:
                    self.logger.error(f"整理失败，已达最大重试次数: {filename}")
            
        except Exception as e:
            self.logger.error(f"执行操作失败: {e}")
    
    @log_performance
    def organize_all_desktop_icons(self) -> Dict[str, Any]:
        """立即整理所有桌面图标"""
        try:
            self.logger.info("开始整理所有桌面图标")
            
            # 获取所有桌面文件
            desktop_files = []
            for item in os.listdir(self.desktop_path):
                item_path = os.path.join(self.desktop_path, item)
                if os.path.isfile(item_path):
                    desktop_files.append(item_path)
            
            # 统计信息
            results = {
                'total_files': len(desktop_files),
                'organized_files': 0,
                'failed_files': 0,
                'skipped_files': 0,
                'rules_applied': defaultdict(int)
            }
            
            # 逐个处理文件
            for filepath in desktop_files:
                try:
                    # 查找匹配规则
                    rule = self.rule_engine.find_matching_rule(filepath)
                    
                    if not rule:
                        results['skipped_files'] += 1
                        continue
                    
                    # 执行放置
                    filename = os.path.basename(filepath)
                    success = self.placement_engine.place_icon_in_region(filename, rule.target_region)
                    
                    if success:
                        results['organized_files'] += 1
                        results['rules_applied'][rule.name] += 1
                    else:
                        results['failed_files'] += 1
                        
                except Exception as e:
                    self.logger.warning(f"处理文件失败 {filepath}: {e}")
                    results['failed_files'] += 1
            
            self.logger.info(f"桌面整理完成: {results['organized_files']}/{results['total_files']} 成功")
            return results
            
        except Exception as e:
            self.logger.error(f"整理所有图标失败: {e}")
            return {'error': str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        try:
            runtime = datetime.now() - self.stats['start_time']
            
            return {
                'runtime_hours': runtime.total_seconds() / 3600,
                'processed_files': self.stats['processed_files'],
                'successful_moves': self.stats['successful_moves'],
                'failed_moves': self.stats['failed_moves'],
                'success_rate': (
                    self.stats['successful_moves'] / max(1, self.stats['processed_files']) * 100
                ),
                'pending_operations': len(self.pending_operations),
                'monitoring_active': self.observer.is_alive() if self.observer else False
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}


# ==================== 全局实例和便捷函数 ====================

_execution_engine_instance: Optional[ExecutionEngine] = None


def get_execution_engine() -> ExecutionEngine:
    """获取全局执行引擎实例"""
    global _execution_engine_instance
    if _execution_engine_instance is None:
        _execution_engine_instance = ExecutionEngine()
    return _execution_engine_instance


def start_desktop_monitoring() -> bool:
    """开始桌面监控"""
    return get_execution_engine().start_monitoring()


def stop_desktop_monitoring() -> None:
    """停止桌面监控"""
    get_execution_engine().stop_monitoring()


def organize_desktop_now() -> Dict[str, Any]:
    """立即整理桌面"""
    return get_execution_engine().organize_all_desktop_icons()


if __name__ == "__main__":
    # 测试代码
    print("=== Aether Desktop 执行引擎测试 ===")
    
    try:
        engine = get_execution_engine()
        print("执行引擎初始化成功")
        
        # 测试启动监控
        print("\n启动桌面监控...")
        if engine.start_monitoring():
            print("监控启动成功")
            
            # 运行5秒钟
            print("监控运行中... (5秒)")
            time.sleep(5)
            
            # 停止监控
            print("停止监控...")
            engine.stop_monitoring()
            print("监控已停止")
        else:
            print("监控启动失败")
        
        # 显示统计信息
        stats = engine.get_statistics()
        print(f"\n统计信息: {stats}")
        
        print("\n测试完成!")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
