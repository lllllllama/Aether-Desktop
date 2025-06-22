#!/usr/bin/env python3
"""测试OpenRouter生成原始规则数据"""

from utils.ai_providers import ai_manager
import json

def test_raw_openrouter():
    """测试OpenRouter生成的原始数据"""
    print("🚀 测试OpenRouter原始规则生成")
    print("=" * 50)
    
    # 切换到OpenRouter
    ai_manager.switch_provider("openrouter")
    provider_info = ai_manager.get_current_provider_info()
    print(f"🤖 当前提供商: {provider_info['name']} ({provider_info['model']})")
    
    # 模拟桌面快照数据
    mock_snapshot = {
        "total_files": 45,
        "file_type_summary": {
            "document": 15,
            "shortcut": 20,
            "executable": 8,
            "image": 2
        },
        "files": [
            {"name": "document.pdf", "type": "document"},
            {"name": "photo.jpg", "type": "image"},
            {"name": "app.exe", "type": "executable"},
            {"name": "shortcut.lnk", "type": "shortcut"}
        ]
    }
    
    # 构建提示词
    prompt = f"""
请根据以下桌面文件信息，生成智能整理规则的JSON格式：

桌面文件统计：
- 总文件数：{mock_snapshot['total_files']}
- 文件类型分布：{mock_snapshot['file_type_summary']}

请生成JSON格式的整理规则，包含以下结构：
{{
  "regions": {{
    "区域名": {{"x_range": [起始x, 结束x], "y_range": [起始y, 结束y]}}
  }},
  "rules": [
    {{"pattern": "文件模式", "target_region": "目标区域"}}
  ]
}}

只返回JSON，不要包含任何解释文字。
"""
    
    print("📤 发送提示词...")
    print(f"提示词长度: {len(prompt)} 字符")
    
    # 调用AI生成规则
    result = ai_manager.generate_rules(prompt)
    
    print("📥 收到响应:")
    print("=" * 50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 50)
    
    # 分析结果
    if isinstance(result, dict):
        if "regions" in result:
            print(f"✅ 包含regions: {len(result['regions'])} 个")
            for name, coords in result['regions'].items():
                print(f"   - {name}: {coords}")
        
        if "rules" in result:
            print(f"✅ 包含rules: {len(result['rules'])} 条")
            for i, rule in enumerate(result['rules'][:3], 1):
                print(f"   {i}. {rule.get('pattern', 'N/A')} → {rule.get('target_region', 'N/A')}")
    else:
        print("❌ 返回数据不是字典格式")
    
    return result

if __name__ == "__main__":
    test_raw_openrouter()
