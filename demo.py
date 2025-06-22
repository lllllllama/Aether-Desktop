#!/usr/bin/env python3
"""
Aether Desktop 演示脚本
======================

演示智能桌面管家的核心功能，包括：
1. 桌面感知和快照
2. AI规则生成（需要配置API密钥）
3. 文件监控和整理

使用方法：
python demo.py

作者: Aether Desktop Team
版本: 1.0.0
"""

import os
import sys
import time
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from utils.config_manager import get_config
    from utils.logger import get_logger
    from perception import DesktopPerception
    from strategy import get_strategy_engine
    from execution import ExecutionEngine
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("请确保所有依赖都已安装")
    sys.exit(1)

def print_banner():
    """打印欢迎横幅"""
    print("=" * 60)
    print("🤖 Aether Desktop - 智能桌面管家演示")
    print("=" * 60)
    print("基于AI的智能桌面文件整理系统")
    print("采用'云端大脑+本地助理'混合架构")
    print("=" * 60)

def demo_perception():
    """演示桌面感知功能"""
    print("\n📸 演示桌面感知功能")
    print("-" * 40)
    
    try:
        # 初始化感知系统
        perception = DesktopPerception()
        print("✓ 感知系统初始化成功")
          # 创建桌面快照
        print("正在分析桌面状态...")
        snapshot = perception.create_desktop_snapshot()
        
        # 显示快照信息
        print(f"✓ 桌面快照创建成功")
        print(f"  - 总文件数: {snapshot.total_files}")
        print(f"  - 文件类型: {len(snapshot.file_type_summary)} 种")
        print(f"  - 主要类型: {list(snapshot.file_type_summary.keys())[:5]}")
        print(f"  - 捕获时间: {snapshot.timestamp}")
        
        # 保存快照
        snapshot_file = perception.save_snapshot_to_file(snapshot, "demo_snapshot.json")
        print(f"✓ 快照已保存: {snapshot_file}")
        
        return snapshot
        
    except Exception as e:
        print(f"❌ 桌面感知演示失败: {e}")
        return None

def demo_ai_strategy(snapshot):
    """演示AI策略生成功能"""
    print("\n🧠 演示AI策略生成功能")
    print("-" * 40)
    
    try:
        # 检查可用的AI提供商
        from utils.ai_providers import ai_manager
        
        available_providers = ai_manager.get_available_providers()
        provider_info = ai_manager.get_current_provider_info()
        
        print(f"📋 可用的AI提供商: {available_providers}")
        print(f"🤖 当前提供商: {provider_info['name']} ({provider_info['model']})")
        
        if not available_providers:
            print("⚠️  没有可用的AI提供商")
            print("请在 config.ini 中配置以下API密钥之一:")
            print("  - OpenRouter API Key (推荐，支持多种免费模型)")
            print("  - Groq API Key (高速免费)")
            print("演示跳过AI规则生成...")
            return None
        
        # 如果有多个提供商，可以演示切换
        if len(available_providers) > 1:
            print("\n🔄 演示AI提供商切换:")
            for provider_name in available_providers:
                print(f"  - 切换到 {provider_name}")
                ai_manager.switch_provider(provider_name)
                current_info = ai_manager.get_current_provider_info()
                print(f"    ✓ 当前: {current_info['name']} ({current_info['model']})")
            
            # 切换回优先级最高的提供商
            ai_manager.switch_provider(available_providers[0])
            print(f"  → 使用 {available_providers[0]} 进行演示")
        
        # 初始化策略引擎
        strategy_engine = get_strategy_engine()
        print("✓ AI策略引擎初始化成功")
        
        # 生成智能规则
        current_provider = ai_manager.get_current_provider_info()
        print(f"正在调用 {current_provider['name']} API 生成整理规则...")
        print("(这可能需要几秒钟时间)")
        
        user_corrections = {}  # 暂时使用空的用户修正记录
        ruleset = strategy_engine.generate_rules_from_llm(snapshot, user_corrections)
        
        if ruleset:
            print("✅ AI规则生成成功")
            print(f"  - 规则版本: {ruleset.version}")
            print(f"  - 生成时间: {ruleset.generated_at}")
            print(f"  - 规则数量: {len(ruleset.rules)}")
            print(f"  - 置信度: {ruleset.confidence_score:.2f}")
            print(f"  - 规则摘要: {ruleset.summary}")
            
            # 显示前几条规则
            print("\n🔧 生成的整理规则预览:")
            for i, rule in enumerate(ruleset.rules[:3], 1):
                print(f"  {i}. {rule.name}")
                print(f"     描述: {rule.description}")
                print(f"     目标区域: {rule.target_region}")
                print(f"     优先级: {rule.priority}")
            
            if len(ruleset.rules) > 3:
                print(f"     ... 还有 {len(ruleset.rules) - 3} 条规则")
            
            # 保存规则集
            rules_file = strategy_engine.save_rules_to_file(ruleset, "demo_rules.json")
            print(f"✓ 规则集已保存: {rules_file}")
            
            return ruleset
        else:
            print("❌ AI规则生成失败")
            return None
            
    except Exception as e:
        print(f"❌ AI策略演示失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def demo_execution():
    """演示执行引擎功能"""
    print("\n⚙️  演示执行引擎功能")
    print("-" * 40)
    
    try:        # 初始化执行引擎
        organizer = ExecutionEngine()
        print("✓ 执行引擎初始化成功")
        
        # 获取统计信息
        stats = organizer.get_statistics()
        print("📊 执行引擎统计:")
        print(f"  - 运行时间: {stats['runtime_hours']:.2f} 小时")
        print(f"  - 处理文件: {stats['processed_files']} 个")
        print(f"  - 成功移动: {stats['successful_moves']} 个")
        print(f"  - 失败移动: {stats['failed_moves']} 个")
        print(f"  - 成功率: {stats['success_rate']:.1f}%")
        print(f"  - 监控状态: {'活跃' if stats['monitoring_active'] else '停止'}")
        
        print("✓ 执行引擎基本功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 执行引擎演示失败: {e}")
        return False

def demo_file_monitoring():
    """演示文件监控功能"""
    print("\n👁️  演示文件监控功能")
    print("-" * 40)
    
    print("文件监控功能演示:")
    print("- 实时监控桌面文件变化")
    print("- 自动触发智能整理规则")
    print("- 支持文件创建、移动、删除事件")
    print("- 可在主程序中启用完整监控")
    print("✓ 监控架构已就绪")

def show_project_info():
    """显示项目信息"""
    print("\n📋 项目架构信息")
    print("-" * 40)
    
    components = [
        ("感知层", "perception.py", "桌面状态采集和快照"),
        ("认知层", "strategy.py", "AI规则生成和决策"),
        ("执行层", "execution.py", "文件监控和自动整理"),
        ("应用层", "main.py", "系统托盘UI和用户交互"),
        ("工具层", "utils/", "配置管理、日志、图标管理"),
    ]
    
    for name, file, desc in components:
        print(f"✓ {name:8} ({file:15}) - {desc}")
    
    print("\n🔧 技术特点:")
    features = [
        "模块化设计，松耦合架构",
        "基于Pydantic的数据验证",
        "Gemini AI驱动的智能决策",
        "Watchdog文件系统监控",
        "系统托盘集成UI",
        "健壮的错误处理和日志",
    ]
    
    for feature in features:
        print(f"  • {feature}")

def main():
    """主演示函数"""
    print_banner()
    
    try:
        # 演示各个模块
        snapshot = demo_perception()
        if snapshot:
            demo_ai_strategy(snapshot)
        
        demo_execution()
        demo_file_monitoring()
        show_project_info()        
        print("\n" + "=" * 60)
        print("🎉 演示完成！")
        print("=" * 60)
        
        print("\n🚀 下一步操作:")
        print("1. 配置AI API密钥 (config.ini):")
        print("   - OpenRouter API Key (推荐) - 支持多种免费模型")
        print("   - Groq API Key - 高速免费模型")
        print("2. 运行 python main.py 启动完整应用")
        print("3. 运行 python test_openrouter.py 测试OpenRouter API")
        print("4. 检查系统托盘中的应用图标")
        print("5. 使用右键菜单进行桌面整理")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
