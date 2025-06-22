"""
Aether Desktop 测试脚本
=====================

用于测试项目各个模块的功能是否正常工作。

测试内容:
1. 配置系统测试
2. 日志系统测试  
3. 感知系统测试
4. 图标管理器测试
5. 模块集成测试

使用方法:
python test_aether.py
"""

import os
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试模块导入"""
    print("=== 测试模块导入 ===")
    
    try:
        print("导入配置管理器...", end=" ")
        from utils.config_manager import get_config
        print("✓")
        
        print("导入日志系统...", end=" ")
        from utils.logger import setup_logger, get_logger
        print("✓")
        
        print("导入感知系统...", end=" ")
        from perception import get_perception
        print("✓")
        
        print("导入执行引擎...", end=" ")
        from execution import get_execution_engine
        print("✓")
        
        print("所有核心模块导入成功!")
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return False

def test_config_system():
    """测试配置系统"""
    print("\n=== 测试配置系统 ===")
    
    try:
        from utils.config_manager import get_config
        
        config = get_config()
        
        print("测试基本配置读取...", end=" ")
        ai_config = config.ai_config
        desktop_config = config.desktop_config
        print("✓")
        
        print("测试配置验证...", end=" ")
        is_valid = config.validate_config()
        print("✓" if is_valid else "! (某些配置可能无效)")
        
        print(f"AI配置: {ai_config['ai_provider']}")
        print(f"桌面路径: {desktop_config['desktop_path']}")
        print(f"自动整理: {desktop_config['auto_organize']}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置系统测试失败: {e}")
        return False

def test_logging_system():
    """测试日志系统"""
    print("\n=== 测试日志系统 ===")
    
    try:
        from utils.logger import setup_logger, get_logger
        
        print("初始化日志系统...", end=" ")
        setup_logger(
            log_level="DEBUG",
            log_file="logs/test.log",
            enable_console=False
        )
        print("✓")
        
        print("测试日志记录...", end=" ")
        logger = get_logger("TestLogger")
        logger.debug("这是一条调试信息")
        logger.info("这是一条信息")
        logger.warning("这是一条警告")
        print("✓")
        
        print("检查日志文件...", end=" ")
        log_file = Path("logs/test.log")
        if log_file.exists() and log_file.stat().st_size > 0:
            print("✓")
        else:
            print("! (日志文件未生成或为空)")
        
        return True
        
    except Exception as e:
        print(f"✗ 日志系统测试失败: {e}")
        return False

def test_perception_system():
    """测试感知系统"""
    print("\n=== 测试感知系统 ===")
    
    try:
        from perception import get_perception, create_snapshot
        
        print("初始化感知系统...", end=" ")
        perception = get_perception()
        print("✓")
        
        print("创建桌面快照...", end=" ")
        snapshot = create_snapshot()
        print("✓")
        
        print(f"快照信息:")
        print(f"  - 总文件数: {snapshot.total_files}")
        print(f"  - 文件类型: {list(snapshot.file_type_summary.keys())}")
        print(f"  - 屏幕分辨率: {snapshot.screen_resolution}")
        
        print("保存快照到文件...", end=" ")
        filepath = perception.save_snapshot_to_file(snapshot, "test_snapshot.json")
        print("✓")
        print(f"快照已保存: {filepath}")
        
        return True
        
    except Exception as e:
        print(f"✗ 感知系统测试失败: {e}")
        return False

def test_icon_manager():
    """测试图标管理器"""
    print("\n=== 测试图标管理器 ===")
    
    try:
        from utils.icon_manager import get_icon_manager
        
        print("初始化图标管理器...", end=" ")
        icon_manager = get_icon_manager()
        print("✓")
        
        print("获取桌面区域...", end=" ")
        regions = icon_manager.get_desktop_regions()
        print("✓")
        
        print(f"桌面区域数量: {len(regions)}")
        for region in regions:
            print(f"  - {region.name}: ({region.x}, {region.y}) {region.width}x{region.height}")
        
        print("获取图标位置...", end=" ")
        icons = icon_manager.get_all_icon_positions()
        print("✓")
        print(f"检测到 {len(icons)} 个图标")
        
        return True
        
    except Exception as e:
        print(f"✗ 图标管理器测试失败: {e}")
        return False

def test_execution_engine():
    """测试执行引擎"""
    print("\n=== 测试执行引擎 ===")
    
    try:
        from execution import get_execution_engine
        
        print("初始化执行引擎...", end=" ")
        engine = get_execution_engine()
        print("✓")
        
        print("获取统计信息...", end=" ")
        stats = engine.get_statistics()
        print("✓")
        
        print(f"执行引擎统计:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
        
        # 不启动实际监控，避免干扰
        print("执行引擎基本功能正常")
        
        return True
        
    except Exception as e:
        print(f"✗ 执行引擎测试失败: {e}")
        return False

def test_file_operations():
    """测试文件操作"""
    print("\n=== 测试文件操作 ===")
    
    try:
        # 检查项目结构
        print("检查项目结构...", end=" ")
        required_dirs = ["utils", "data", "assets", "tests"]
        required_files = ["main.py", "perception.py", "strategy.py", "execution.py", "config.ini", "requirements.txt"]
        
        missing_items = []
        
        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                missing_items.append(f"目录: {dir_name}")
        
        for file_name in required_files:
            if not Path(file_name).exists():
                missing_items.append(f"文件: {file_name}")
        
        if missing_items:
            print(f"! 缺少项目文件:")
            for item in missing_items:
                print(f"    - {item}")
        else:
            print("✓")
        
        # 检查数据文件
        print("检查数据文件...", end=" ")
        data_files = ["desktop_regions.json", "user_corrections.json"]
        
        for file_name in data_files:
            file_path = Path("data") / file_name
            if file_path.exists():
                print(f"✓ {file_name}")
            else:
                print(f"! {file_name} 不存在")
        
        return len(missing_items) == 0
        
    except Exception as e:
        print(f"✗ 文件操作测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 Aether Desktop 功能测试开始")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置系统", test_config_system), 
        ("日志系统", test_logging_system),
        ("感知系统", test_perception_system),
        ("图标管理器", test_icon_manager),
        ("执行引擎", test_execution_engine),
        ("文件操作", test_file_operations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:15} : {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！Aether Desktop 准备就绪")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关问题")
        return False

def main():
    """主函数"""
    try:
        success = run_all_tests()
        
        if success:
            print("\n" + "=" * 50)
            print("🎯 下一步操作建议:")
            print("1. 在 config.ini 中配置 Gemini API 密钥")
            print("2. 运行 python main.py 启动应用程序")
            print("3. 查看系统托盘中的 Aether Desktop 图标")
            print("4. 尝试 '立即优化桌面' 功能")
            
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
