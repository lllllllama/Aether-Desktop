"""
Groq AI API 测试脚本
==================
"""

import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_groq_api():
    """测试Groq API功能"""
    try:
        from utils.ai_providers import ai_manager
        from utils.logger import setup_logger, get_logger
        from utils.config_manager import get_config
        
        # 设置日志
        setup_logger(log_level="INFO", enable_console=True)
        logger = get_logger(__name__)
        
        logger.info("开始测试Groq AI API...")
        
        # 构建测试提示词
        prompt = """
根据以下桌面文件信息生成整理规则：

文件列表:
- document.pdf (PDF文档, 1MB)
- photo.jpg (图片文件, 2MB)  
- video.mp4 (视频文件, 10MB)
- archive.zip (压缩包, 5MB)
- program.exe (可执行文件, 3MB)

桌面分辨率: 1920x1080

请生成JSON格式的整理规则，将不同类型的文件分配到不同的桌面区域。

要求的JSON结构：
{
    "regions": {
        "documents": {"x_range": [0, 300], "y_range": [0, 200]},
        "images": {"x_range": [300, 600], "y_range": [0, 200]}
    },
    "rules": [
        {"pattern": "*.pdf", "target_region": "documents"},
        {"pattern": "*.jpg", "target_region": "images"}
    ],
    "metadata": {
        "generated_by": "groq_ai",
        "generation_time": "2025-06-22T10:00:00",
        "confidence": 0.9
    }
}
"""
        
        # 测试AI规则生成
        logger.info("调用Groq AI生成规则...")
        rules = ai_manager.generate_rules(prompt)
        
        logger.info("AI规则生成成功!")
        print("\n🎉 生成的规则:")
        print("=" * 50)
        print(json.dumps(rules, indent=2, ensure_ascii=False))
        print("=" * 50)
        
        # 验证规则结构
        required_keys = ["regions", "rules"]
        for key in required_keys:
            if key not in rules:
                logger.warning(f"规则缺少必需的键: {key}")
            else:
                logger.info(f"✓ 包含 {key}: {len(rules[key])} 项")
        
        # 检查区域定义
        if "regions" in rules:
            for region_name, region_def in rules["regions"].items():
                if "x_range" in region_def and "y_range" in region_def:
                    logger.info(f"✓ 区域 {region_name}: x{region_def['x_range']} y{region_def['y_range']}")
                else:
                    logger.warning(f"区域 {region_name} 定义不完整")
        
        return True
        
    except Exception as e:
        print(f"❌ Groq API测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_config():
    """检查配置"""
    try:
        from utils.config_manager import get_config
        
        config = get_config()
        api_key = config.get("AI_CONFIG", "groq_api_key", fallback="").strip()
        
        print("🔍 配置检查:")
        print("-" * 30)
        
        if not api_key:
            print("❌ 未发现API密钥")
            print("📝 请在 config.ini 中配置 groq_api_key")
            return False
        else:
            print(f"✅ API密钥: {api_key[:10]}...{api_key[-4:]}")
            return True
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Groq AI 集成测试")
    print("=" * 50)
    
    # 检查配置
    if check_config():
        # 运行测试
        success = test_groq_api()
        
        if success:
            print("\n🎉 Groq AI集成测试成功!")
            print("💡 现在可以运行完整的应用程序")
            print("   python main.py")
        else:
            print("\n❌ 测试失败，请检查API密钥和网络连接")
    else:
        print("⚙️ 请先配置API密钥")
