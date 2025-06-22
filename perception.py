"""
感知层 - Aether Desktop
=====================

桌面状态感知系统，负责采集完整的桌面环境信息，为AI大脑提供决策依据。

核心功能:
1. 扫描桌面文件和图标位置
2. 分析文件属性（类型、大小、创建时间等）
3. 生成桌面状态快照
4. 加载用户修正记录
5. 监控桌面变化

作者: Aether Desktop Team
版本: 1.0.0
"""

import os
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from utils.logger import get_logger, log_performance, log_exception
from utils.config_manager import get_config


@dataclass
class FileInfo:
    """文件信息数据结构"""
    filename: str
    filepath: str
    file_type: str
    extension: str
    size_bytes: int
    size_mb: float
    created_time: str
    modified_time: str
    accessed_time: str
    is_shortcut: bool
    target_path: Optional[str] = None


@dataclass
class DesktopSnapshot:
    """桌面状态快照"""
    timestamp: str
    desktop_path: str
    screen_resolution: Dict[str, int]
    total_files: int
    files: List[FileInfo]
    icon_positions: Dict[str, Dict[str, Any]]
    regions: List[Dict[str, Any]]
    file_type_summary: Dict[str, int]
    size_distribution: Dict[str, int]


class DesktopPerception:
    """桌面感知系统"""
    
    def __init__(self):
        """初始化感知系统"""
        self.logger = get_logger(self.__class__.__name__)
        self.config = get_config()
        
        try:
            from utils.icon_manager import get_icon_manager
            self.icon_manager = get_icon_manager()
        except Exception as e:
            self.logger.warning(f"图标管理器初始化失败: {e}")
            self.icon_manager = None
            
        self.desktop_path = self.config.desktop_config['desktop_path']
        
        # 支持的文件扩展名
        self.supported_extensions = set(self.config.file_config['supported_extensions'])
        
        self.logger.info("桌面感知系统初始化完成")
        self.logger.debug(f"监控路径: {self.desktop_path}")
    
    @log_performance
    def create_desktop_snapshot(self) -> DesktopSnapshot:
        """创建完整的桌面状态快照
        
        Returns:
            桌面状态快照对象
        """
        try:
            self.logger.info("开始创建桌面状态快照")
            
            # 获取当前时间戳
            timestamp = datetime.now().isoformat()
            
            # 扫描桌面文件
            files = self._scan_desktop_files()
            
            # 获取图标位置信息
            icon_positions = self._get_icon_positions_dict()
            
            # 获取桌面区域定义
            regions = self._get_regions_dict()
            
            # 获取屏幕分辨率
            screen_resolution = {
                'width': self.icon_manager.screen_width,
                'height': self.icon_manager.screen_height
            }
            
            # 生成文件类型统计
            file_type_summary = self._analyze_file_types(files)
            
            # 生成大小分布统计
            size_distribution = self._analyze_size_distribution(files)
            
            # 创建快照对象
            snapshot = DesktopSnapshot(
                timestamp=timestamp,
                desktop_path=self.desktop_path,
                screen_resolution=screen_resolution,
                total_files=len(files),
                files=files,
                icon_positions=icon_positions,
                regions=regions,
                file_type_summary=file_type_summary,
                size_distribution=size_distribution
            )
            
            self.logger.info(f"桌面快照创建完成: {len(files)} 个文件")
            return snapshot
            
        except Exception as e:
            self.logger.error(f"创建桌面快照失败: {e}")
            raise
    
    def _scan_desktop_files(self) -> List[FileInfo]:
        """扫描桌面文件"""
        files = []
        
        try:
            if not os.path.exists(self.desktop_path):
                self.logger.warning(f"桌面路径不存在: {self.desktop_path}")
                return files
            
            # 遍历桌面目录
            for item in os.listdir(self.desktop_path):
                try:
                    item_path = os.path.join(self.desktop_path, item)
                    
                    # 跳过目录
                    if os.path.isdir(item_path):
                        continue
                    
                    # 检查文件扩展名
                    _, ext = os.path.splitext(item)
                    if ext.lower() not in self.supported_extensions:
                        continue
                    
                    # 获取文件信息
                    file_info = self._get_file_info(item_path)
                    if file_info:
                        files.append(file_info)
                        
                except Exception as e:
                    self.logger.warning(f"处理文件失败 {item}: {e}")
                    continue
            
            self.logger.debug(f"扫描到 {len(files)} 个有效文件")
            return files
            
        except Exception as e:
            self.logger.error(f"扫描桌面文件失败: {e}")
            return files
    
    def _get_file_info(self, filepath: str) -> Optional[FileInfo]:
        """获取单个文件的详细信息"""
        try:
            stat = os.stat(filepath)
            filename = os.path.basename(filepath)
            _, extension = os.path.splitext(filename)
            
            # 获取时间信息
            created_time = datetime.fromtimestamp(stat.st_ctime).isoformat()
            modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
            accessed_time = datetime.fromtimestamp(stat.st_atime).isoformat()
            
            # 判断文件类型
            is_shortcut = extension.lower() == '.lnk'
            file_type = self._determine_file_type(extension)
            
            # 获取快捷方式目标路径
            target_path = None
            if is_shortcut:
                target_path = self._get_shortcut_target(filepath)
            
            return FileInfo(
                filename=filename,
                filepath=filepath,
                file_type=file_type,
                extension=extension.lower(),
                size_bytes=stat.st_size,
                size_mb=round(stat.st_size / (1024 * 1024), 2),
                created_time=created_time,
                modified_time=modified_time,
                accessed_time=accessed_time,
                is_shortcut=is_shortcut,
                target_path=target_path
            )
            
        except Exception as e:
            self.logger.warning(f"获取文件信息失败 {filepath}: {e}")
            return None
    
    def _determine_file_type(self, extension: str) -> str:
        """根据扩展名确定文件类型"""
        ext = extension.lower()
        
        type_mapping = {
            # 文档类型
            '.txt': 'document',
            '.doc': 'document',
            '.docx': 'document', 
            '.pdf': 'document',
            '.rtf': 'document',
            
            # 图片类型
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.gif': 'image',
            '.bmp': 'image',
            '.ico': 'image',
            
            # 视频类型
            '.mp4': 'video',
            '.avi': 'video',
            '.mkv': 'video',
            '.mov': 'video',
            
            # 音频类型
            '.mp3': 'audio',
            '.wav': 'audio',
            '.flac': 'audio',
            
            # 压缩文件
            '.zip': 'archive',
            '.rar': 'archive',
            '.7z': 'archive',
            
            # 可执行文件
            '.exe': 'executable',
            '.msi': 'executable',
            
            # 快捷方式
            '.lnk': 'shortcut'
        }
        
        return type_mapping.get(ext, 'other')
    
    def _get_shortcut_target(self, shortcut_path: str) -> Optional[str]:
        """获取快捷方式的目标路径"""
        try:
            # 这里需要使用Windows COM接口来获取快捷方式目标
            # 目前先返回None，后续可以实现
            return None
        except Exception as e:
            self.logger.debug(f"获取快捷方式目标失败 {shortcut_path}: {e}")
            return None
    
    def _get_icon_positions_dict(self) -> Dict[str, Dict[str, Any]]:
        """获取图标位置信息字典"""
        try:
            icons = self.icon_manager.get_all_icon_positions()
            return {
                filename: {
                    'x': info.x,
                    'y': info.y,
                    'width': info.width,
                    'height': info.height,
                    'display_name': info.display_name
                }
                for filename, info in icons.items()
            }
        except Exception as e:
            self.logger.warning(f"获取图标位置失败: {e}")
            return {}
    
    def _get_regions_dict(self) -> List[Dict[str, Any]]:
        """获取桌面区域定义"""
        try:
            regions = self.icon_manager.get_desktop_regions()
            return [
                {
                    'id': region.id,
                    'name': region.name,
                    'x': region.x,
                    'y': region.y,
                    'width': region.width,
                    'height': region.height,
                    'grid_size': region.grid_size,
                    'margin': region.margin
                }
                for region in regions
            ]
        except Exception as e:
            self.logger.warning(f"获取桌面区域失败: {e}")
            return []
    
    def _analyze_file_types(self, files: List[FileInfo]) -> Dict[str, int]:
        """分析文件类型分布"""
        type_count = {}
        for file in files:
            file_type = file.file_type
            type_count[file_type] = type_count.get(file_type, 0) + 1
        return type_count
    
    def _analyze_size_distribution(self, files: List[FileInfo]) -> Dict[str, int]:
        """分析文件大小分布"""
        size_ranges = {
            'tiny': 0,      # < 1MB
            'small': 0,     # 1-10MB
            'medium': 0,    # 10-100MB
            'large': 0,     # 100MB-1GB
            'huge': 0       # > 1GB
        }
        
        for file in files:
            size_mb = file.size_mb
            if size_mb < 1:
                size_ranges['tiny'] += 1
            elif size_mb < 10:
                size_ranges['small'] += 1
            elif size_mb < 100:
                size_ranges['medium'] += 1
            elif size_mb < 1000:
                size_ranges['large'] += 1
            else:
                size_ranges['huge'] += 1
        
        return size_ranges
    
    @log_performance
    def load_user_corrections(self) -> Dict[str, Any]:
        """加载用户修正记录
        
        Returns:
            用户修正数据字典
        """
        try:
            corrections_file = os.path.join(
                os.path.dirname(self.desktop_path), 
                'data', 
                'user_corrections.json'
            )
            
            if os.path.exists(corrections_file):
                with open(corrections_file, 'r', encoding='utf-8') as f:
                    corrections = json.load(f)
                self.logger.info(f"加载用户修正记录: {len(corrections)} 条")
                return corrections
            else:
                self.logger.info("用户修正记录文件不存在，返回空记录")
                return {}
                
        except Exception as e:
            self.logger.error(f"加载用户修正记录失败: {e}")
            return {}
    
    def save_snapshot_to_file(self, snapshot: DesktopSnapshot, filename: Optional[str] = None) -> str:
        """保存快照到文件
        
        Args:
            snapshot: 桌面快照对象
            filename: 可选的文件名
            
        Returns:
            保存的文件路径
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"desktop_snapshot_{timestamp}.json"
            
            # 确保data目录存在
            data_dir = os.path.join(os.path.dirname(self.desktop_path), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            filepath = os.path.join(data_dir, filename)
            
            # 转换为字典并保存
            snapshot_dict = asdict(snapshot)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(snapshot_dict, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"桌面快照已保存: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"保存桌面快照失败: {e}")
            raise
    
    def load_snapshot_from_file(self, filepath: str) -> Optional[DesktopSnapshot]:
        """从文件加载快照
        
        Args:
            filepath: 快照文件路径
            
        Returns:
            桌面快照对象或None
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 重建FileInfo对象列表
            files = [FileInfo(**file_data) for file_data in data['files']]
            data['files'] = files
            
            snapshot = DesktopSnapshot(**data)
            self.logger.info(f"桌面快照已加载: {filepath}")
            return snapshot
            
        except Exception as e:
            self.logger.error(f"加载桌面快照失败: {e}")
            return None
    
    def compare_snapshots(self, old_snapshot: DesktopSnapshot, new_snapshot: DesktopSnapshot) -> Dict[str, Any]:
        """比较两个快照的差异
        
        Args:
            old_snapshot: 旧快照
            new_snapshot: 新快照
            
        Returns:
            差异报告字典
        """
        try:
            # 文件变化分析
            old_files = {f.filename: f for f in old_snapshot.files}
            new_files = {f.filename: f for f in new_snapshot.files}
            
            added_files = set(new_files.keys()) - set(old_files.keys())
            removed_files = set(old_files.keys()) - set(new_files.keys())
            common_files = set(old_files.keys()) & set(new_files.keys())
            
            # 位置变化分析
            position_changes = {}
            for filename in common_files:
                old_pos = old_snapshot.icon_positions.get(filename, {})
                new_pos = new_snapshot.icon_positions.get(filename, {})
                
                if old_pos and new_pos:
                    if old_pos.get('x') != new_pos.get('x') or old_pos.get('y') != new_pos.get('y'):
                        position_changes[filename] = {
                            'old': old_pos,
                            'new': new_pos
                        }
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'file_changes': {
                    'added': list(added_files),
                    'removed': list(removed_files),
                    'total_changes': len(added_files) + len(removed_files)
                },
                'position_changes': position_changes,
                'total_position_changes': len(position_changes)
            }
            
            self.logger.info(f"快照比较完成: {report['file_changes']['total_changes']} 文件变化, {report['total_position_changes']} 位置变化")
            return report
            
        except Exception as e:
            self.logger.error(f"快照比较失败: {e}")
            return {}


# 全局实例
_perception_instance: Optional[DesktopPerception] = None


def get_perception() -> DesktopPerception:
    """获取全局感知系统实例"""
    global _perception_instance
    if _perception_instance is None:
        _perception_instance = DesktopPerception()
    return _perception_instance


# 便捷函数
def create_snapshot() -> DesktopSnapshot:
    """创建桌面状态快照"""
    return get_perception().create_desktop_snapshot()


def get_user_corrections() -> Dict[str, Any]:
    """获取用户修正记录"""
    return get_perception().load_user_corrections()


if __name__ == "__main__":
    # 测试代码
    print("=== Aether Desktop 感知系统测试 ===")
    
    try:
        perception = get_perception()
        
        # 创建桌面快照
        print("\n1. 创建桌面快照...")
        snapshot = perception.create_desktop_snapshot()
        print(f"快照创建成功: {snapshot.total_files} 个文件")
        
        # 显示文件类型统计
        print("\n2. 文件类型统计:")
        for file_type, count in snapshot.file_type_summary.items():
            print(f"  {file_type}: {count}")
        
        # 显示大小分布
        print("\n3. 文件大小分布:")
        for size_range, count in snapshot.size_distribution.items():
            print(f"  {size_range}: {count}")
        
        # 保存快照
        print("\n4. 保存快照...")
        filepath = perception.save_snapshot_to_file(snapshot)
        print(f"快照已保存: {filepath}")
        
        print("\n测试完成!")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
