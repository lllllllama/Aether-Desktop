#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenRouter API 集成测试
======================
测试OpenRouter API的连接性和规则生成能力
"""

import os
import sys
import traceback
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.ai_providers import OpenRouterProvider, ai_manager
from utils.logger import get_logger
from utils.config_manager import get_config

def test_openrouter_api():
    """测试OpenRouter API直接调用"""
    logger = get_logger(__name__)
    
    # 用于测试的API Key (用户需要自己配置)
    # 注意：这里需要用户在config.ini中配置真实的OpenRouter API Key
    config = get_config()
    api_key = config.get("AI_CONFIG", "openrouter_api_key", fallback="").strip()
    
    if not api_key or api_key == "YOUR_OPENROUTER_API_KEY_HERE":
        print("❌ 请在config.ini中配置有效的OpenRouter API Key")
        print("💡 获取免费API Key: https://openrouter.ai/")
        print("   - 注册账户")
        print("   - 获取API Key")
        print("   - 使用免费模型如: meta-llama/llama-3.1-8b-instruct:free")
        return False
    
    try:
        print("🔄 测试OpenRouter API连接...")
        
        # 创建OpenRouter提供商
        model = config.get("AI_CONFIG", "openrouter_model", fallback="meta-llama/llama-3.1-8b-instruct:free")
        provider = OpenRouterProvider(api_key, model)
        
        # 测试用的prompt
        test_prompt = """
我的桌面有以下文件：
- report.pdf (工作文档)
- vacation.jpg (度假照片)  
- music.mp3 (音乐文件)
- installer.exe (安装程序)
- notes.txt (笔记)

请生成JSON格式的桌面整理规则，包含regions和rules两个部分。
        """
        
        print(f"📡 正在调用OpenRouter API (模型: {model})...")
        result = provider.generate_rules(test_prompt)
        
        if result and "rules" in result:
            print("✅ OpenRouter API测试成功!")
            print(f"📋 生成的规则数量: {len(result.get('rules', []))}")
            print(f"🗂️ 定义的区域数量: {len(result.get('regions', {}))}")
            
            # 显示生成的规则摘要
            if "metadata" in result:
                metadata = result["metadata"]
                print(f"🤖 规则生成器: {metadata.get('generated_by', 'unknown')}")
                print(f"⏰ 生成时间: {metadata.get('generation_time', 'unknown')}")
                print(f"🎯 置信度: {metadata.get('confidence', 'unknown')}")
            
            return True
        else:
            print("❌ OpenRouter API返回结果异常")
            print(f"📝 返回内容: {result}")
            return False
            
    except Exception as e:
        print(f"❌ OpenRouter API测试失败: {e}")
        print(f"🔍 详细错误信息:")
        traceback.print_exc()
        return False

def test_ai_manager_openrouter():
    """测试AI管理器中的OpenRouter集成"""
    logger = get_logger(__name__)
    
    try:
        print("\n🔄 测试AI管理器的OpenRouter集成...")
        
        # 检查可用的提供商
        available_providers = ai_manager.get_available_providers()
        print(f"📋 可用的AI提供商: {available_providers}")
        
        if "openrouter" not in available_providers:
            print("❌ OpenRouter提供商未注册")
            return False
        
        # 切换到OpenRouter
        if ai_manager.switch_provider("openrouter"):
            print("✅ 成功切换到OpenRouter提供商")
        else:
            print("❌ 切换到OpenRouter提供商失败")
            return False
        
        # 获取当前提供商信息
        provider_info = ai_manager.get_current_provider_info()
        print(f"🤖 当前提供商: {provider_info['name']} ({provider_info['model']})")
        
        # 测试规则生成
        test_prompt = """
我的桌面文件情况：
- 有很多PDF文档散乱分布
- 有一些图片文件(jpg, png)
- 有几个音频文件(mp3)
- 有一些下载的软件(exe, zip)

请根据文件类型生成智能的桌面区域规划和整理规则。
        """
        
        print("📡 通过AI管理器调用OpenRouter...")
        result = ai_manager.generate_rules(test_prompt)
        
        if result and "rules" in result:
            print("✅ AI管理器OpenRouter集成测试成功!")
            print(f"📋 生成的规则数量: {len(result.get('rules', []))}")
            
            # 显示部分规则作为示例
            rules = result.get("rules", [])[:3]  # 只显示前3条
            print("📄 规则示例:")
            for i, rule in enumerate(rules, 1):
                print(f"   {i}. {rule.get('pattern', '?')} → {rule.get('target_region', '?')}")
            
            return True
        else:
            print("❌ AI管理器返回结果异常")
            return False
            
    except Exception as e:
        print(f"❌ AI管理器OpenRouter测试失败: {e}")
        traceback.print_exc()
        return False

def test_openrouter_models():
    """测试不同的OpenRouter免费模型"""
    logger = get_logger(__name__)
    config = get_config()
    api_key = config.get("AI_CONFIG", "openrouter_api_key", fallback="").strip()
    
    if not api_key or api_key == "YOUR_OPENROUTER_API_KEY_HERE":
        print("❌ 请先配置OpenRouter API Key")
        return False
    
    # 可用的免费模型列表
    free_models = [
        "meta-llama/llama-3.1-8b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free",
        "google/gemma-7b-it:free"
    ]
    
    print(f"\n🔄 测试OpenRouter免费模型可用性...")
    
    test_prompt = "请简单回复'测试成功'四个字，验证模型连接正常。"
    
    for model in free_models:
        try:
            print(f"📡 测试模型: {model}")
            provider = OpenRouterProvider(api_key, model)
            result = provider.generate_rules(test_prompt)
            
            if result:
                print(f"✅ {model} - 可用")
            else:
                print(f"❌ {model} - 不可用")
                
        except Exception as e:
            print(f"❌ {model} - 测试失败: {str(e)[:100]}")

def main():
    """主函数"""
    print("🚀 OpenRouter API集成测试")
    print("=" * 50)
    
    # 1. 直接API测试
    success1 = test_openrouter_api()
    
    # 2. AI管理器集成测试
    success2 = test_ai_manager_openrouter()
    
    # 3. 多模型测试
    test_openrouter_models()
    
    print("\n📊 测试结果汇总:")
    print(f"   直接API测试: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"   AI管理器集成: {'✅ 通过' if success2 else '❌ 失败'}")
    
    if success1 and success2:
        print("\n🎉 所有OpenRouter测试通过!")
        print("💡 可以开始使用OpenRouter API生成桌面整理规则了")
    else:
        print("\n⚠️  部分测试失败，请检查:")
        print("   1. OpenRouter API Key是否正确配置")
        print("   2. 网络连接是否正常")
        print("   3. 选择的模型是否可用")

if __name__ == "__main__":
    main()
