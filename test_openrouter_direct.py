#!/usr/bin/env python3
"""直接测试OpenRouter API Key的有效性"""

import requests
import json
from utils.config_manager import get_config

def test_openrouter_direct():
    """直接测试OpenRouter API"""
    config = get_config()
    api_key = config.get("AI_CONFIG", "openrouter_api_key", fallback="").strip()
    model = config.get("AI_CONFIG", "openrouter_model", fallback="meta-llama/llama-3.1-8b-instruct:free")
    
    print(f"🔑 测试API Key: {api_key[:20]}...")
    print(f"🤖 测试模型: {model}")
    print(f"📏 API Key长度: {len(api_key)}")
    
    if not api_key:
        print("❌ API Key为空")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://aether-desktop.com",
        "X-Title": "Aether Desktop"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello, are you working?"}
        ],
        "max_tokens": 50
    }
      try:
        print("🌐 发送请求到OpenRouter...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,  # 使用json参数而不是data
            timeout=30
        )
        
        print(f"📊 状态码: {response.status_code}")
        print(f"📝 响应头: {dict(response.headers)}")
        print(f"📄 响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            print(f"🤖 模型响应: {result.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')}")
            return True
        else:
            print(f"❌ API调用失败: {response.status_code}")
            # 尝试不同的认证格式
            if response.status_code == 401:
                print("🔄 尝试不同的认证格式...")
                
                # 尝试不带Bearer前缀
                alt_headers = {
                    "Authorization": api_key,
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://aether-desktop.com",
                    "X-Title": "Aether Desktop"
                }
                
                alt_response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=alt_headers,
                    json=payload,
                    timeout=30
                )
                
                print(f"📊 替代格式状态码: {alt_response.status_code}")
                print(f"📄 替代格式响应: {alt_response.text}")
                
                if alt_response.status_code == 200:
                    result = alt_response.json()
                    print("✅ 替代格式API调用成功!")
                    print(f"🤖 模型响应: {result.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')}")
                    return True
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    test_openrouter_direct()
