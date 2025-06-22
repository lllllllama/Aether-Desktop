#!/usr/bin/env python3
"""测试OpenRouter的免费模型可用性"""

import requests
from utils.config_manager import get_config

def test_openrouter_models():
    """测试OpenRouter的免费模型"""
    config = get_config()
    api_key = config.get("AI_CONFIG", "openrouter_api_key", fallback="").strip()
    
    print("🚀 测试OpenRouter免费模型可用性")
    print("=" * 50)
    
    # 常见的免费模型列表
    free_models = [
        "deepseek-ai/deepseek-v3",
        "deepseek-ai/deepseek-v2.5:free",
        "deepseek-ai/deepseek-chat:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free",
        "google/gemma-7b-it:free",
        "qwen/qwen-2-7b-instruct:free",
        "mistralai/mistral-7b-instruct:free"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://aether-desktop.com",
        "X-Title": "Aether Desktop"
    }
    
    payload_template = {
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    
    working_models = []
    
    for model in free_models:
        print(f"📡 测试模型: {model}")
        
        payload = payload_template.copy()
        payload["model"] = model
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"  ✅ {model} - 可用")
                working_models.append(model)
            else:
                print(f"  ❌ {model} - 错误: {response.status_code}")
                if response.status_code == 400:
                    error_data = response.json()
                    print(f"     详情: {error_data.get('error', {}).get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"  ❌ {model} - 异常: {e}")
    
    print("\n📊 测试结果汇总:")
    print(f"✅ 可用模型数量: {len(working_models)}")
    
    if working_models:
        print("🎯 推荐使用的模型:")
        for model in working_models[:3]:  # 显示前3个可用模型
            print(f"  - {model}")
        
        return working_models[0]  # 返回第一个可用模型
    else:
        print("❌ 没有找到可用的免费模型")
        return None

if __name__ == "__main__":
    best_model = test_openrouter_models()
    if best_model:
        print(f"\n🔧 建议配置模型: {best_model}")
    else:
        print("\n⚠️  建议使用Groq API作为备选方案")
