"""
AI策略生成模块 - Aether Desktop
=============================

认知层核心模块，负责与AI大脑（LLM）通信，生成智能整理规则。
这是项目的"智慧核心"，将桌面状态转化为可执行的整理策略。

核心功能:
1. 构建动态AI提示词
2. 与Gemini API安全通信
3. 使用Function Calling生成结构化规则
4. 处理Token限制和错误恢复
5. 验证和优化生成的规则

技术特点:
- 使用Pydantic进行数据验证
- 支持函数调用模式确保输出格式
- 智能提示词工程
- 健壮的错误处理和重试机制

作者: Aether Desktop Team
版本: 1.0.0
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    print("提示: google-generativeai 库未安装，将使用Groq作为AI提供商")
    genai = None

from pydantic import BaseModel, Field, validator
from utils.logger import get_logger, log_performance, log_exception
from utils.config_manager import get_config
from utils.ai_providers import ai_manager
from perception import DesktopSnapshot


# ==================== Pydantic 数据模型 ====================

class IconPlacementRule(BaseModel):
    """图标放置规则"""
    rule_id: str = Field(..., description="规则唯一标识符")
    name: str = Field(..., description="规则名称")
    description: str = Field(..., description="规则描述")
    conditions: Dict[str, Any] = Field(..., description="触发条件")
    target_region: str = Field(..., description="目标区域ID")
    priority: int = Field(default=50, description="优先级(1-100)")
    enabled: bool = Field(default=True, description="是否启用")

class DesktopRuleset(BaseModel):
    """完整的桌面整理规则集"""
    version: str = Field(default="1.0", description="规则版本")
    generated_at: str = Field(..., description="生成时间")
    summary: str = Field(..., description="规则集摘要")
    rules: List[IconPlacementRule] = Field(..., description="具体规则列表")
    confidence_score: float = Field(..., description="置信度分数(0-1)")
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('置信度必须在0-1之间')
        return v


# ==================== AI策略生成器 ====================

class AIStrategyEngine:
    """AI策略生成引擎"""
    
    def __init__(self):
        """初始化AI引擎"""
        self.logger = get_logger(self.__class__.__name__)
        self.config = get_config()
        
        # 获取AI配置
        ai_config = self.config.ai_config
        self.api_key = ai_config.get('gemini_api_key', '')
        self.model_name = ai_config.get('gemini_model', 'gemini-1.5-pro')
        self.max_tokens = ai_config.get('max_tokens', 8192)
        self.temperature = ai_config.get('temperature', 0.7)
        self.use_function_calling = ai_config.get('use_function_calling', True)
        self.max_retries = ai_config.get('max_retry_attempts', 3)
        
        # 优先使用Groq，Gemini作为备用
        self.ai_manager = ai_manager
        
        # 加载提示词模板
        self.prompt_template = self._load_prompt_template()
        
        self.logger.info("AI策略引擎初始化完成 - 使用Groq AI")
    
    def _initialize_gemini(self) -> None:
        """初始化Gemini API"""
        try:
            if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY_HERE":
                raise ValueError("请在config.ini中配置有效的Gemini API密钥")
            
            genai.configure(api_key=self.api_key)
            
            # 创建模型实例
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                }
            )
            
            self.logger.debug(f"Gemini模型初始化: {self.model_name}")
            
        except Exception as e:
            self.logger.error(f"Gemini初始化失败: {e}")
            raise
    
    def _load_prompt_template(self) -> str:
        """加载提示词模板"""
        try:
            template_path = Path(__file__).parent / "assets" / "templates" / "strategy_prompt.txt"
            
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # 使用内置默认模板
                return self._get_default_prompt_template()
                
        except Exception as e:
            self.logger.warning(f"加载提示词模板失败: {e}, 使用默认模板")
            return self._get_default_prompt_template()
    
    def _get_default_prompt_template(self) -> str:
        """获取默认提示词模板"""
        return """
你是 Aether Desktop 的AI大脑，专门负责分析用户的桌面文件布局习惯，生成智能整理规则。

# 角色定义
你是一位世界级的桌面管理专家，拥有以下能力：
- 深度理解用户的文件使用模式
- 基于文件类型、大小、创建时间等属性智能分类
- 考虑桌面空间的最优利用
- 预测用户的使用偏好

# 桌面状态信息
## 当前桌面快照
{desktop_snapshot}

## 用户修正记录
{user_corrections}

## 桌面区域定义
{desktop_regions}

# 任务要求
请基于以上信息，生成一套完整的桌面图标整理规则。规则应该：

1. **智能分类**: 根据文件类型、用途、频率等维度进行分类
2. **空间优化**: 合理利用桌面区域，避免拥挤
3. **用户友好**: 符合用户的使用习惯和直觉
4. **可扩展**: 能够适应未来新增的文件

# 输出格式
请严格按照以下JSON格式输出规则集：

```json
{{
  "version": "1.0",
  "generated_at": "{current_time}",
  "summary": "规则集的简要描述",
  "rules": [
    {{
      "rule_id": "rule_001",
      "name": "规则名称",
      "description": "详细描述",
      "conditions": {{
        "file_type": ["document", "image"],
        "size_range": "small",
        "keywords": ["工作", "项目"]
      }},
      "target_region": "top_left",
      "priority": 80,
      "enabled": true
    }}
  ],
  "confidence_score": 0.85
}}
```

请开始分析并生成规则：
"""
    
    def generate_rules_from_llm(self, snapshot: DesktopSnapshot, corrections: Dict[str, Any]) -> Optional[DesktopRuleset]:
        """从LLM生成整理规则 - 使用Groq AI
        
        Args:
            snapshot: 桌面状态快照
            corrections: 用户修正记录
            
        Returns:
            生成的规则集或None
        """
        try:
            self.logger.info("开始使用Groq AI生成整理规则")
            
            # 构建完整的提示词
            prompt = self._build_groq_prompt(snapshot, corrections)
            
            # 调用Groq AI生成规则
            rules_dict = ai_manager.generate_rules(prompt)
            
            if rules_dict:
                # 转换为Pydantic模型
                ruleset = self._convert_to_pydantic_ruleset(rules_dict)
                
                if ruleset:
                    # 验证和优化规则
                    validated_ruleset = self._validate_and_optimize_rules(ruleset)
                    
                    self.logger.info(f"Groq AI规则生成成功: {len(validated_ruleset.rules)} 条规则")
                    return validated_ruleset
            
            self.logger.error("Groq AI规则生成失败")
            return None
            
        except Exception as e:
            self.logger.error(f"生成AI规则失败: {e}")
            return None
    
    def _build_prompt(self, snapshot: DesktopSnapshot, corrections: Dict[str, Any]) -> str:
        """构建完整的AI提示词"""
        try:
            # 准备桌面快照数据
            snapshot_summary = {
                "timestamp": snapshot.timestamp,
                "total_files": snapshot.total_files,
                "file_types": snapshot.file_type_summary,
                "size_distribution": snapshot.size_distribution,
                "recent_files": [f.filename for f in snapshot.files[:10]]  # 最近的10个文件
            }
            
            # 准备区域信息
            regions_info = snapshot.regions
            
            # 填充模板
            prompt = self.prompt_template.format(
                desktop_snapshot=json.dumps(snapshot_summary, ensure_ascii=False, indent=2),
                user_corrections=json.dumps(corrections, ensure_ascii=False, indent=2),
                desktop_regions=json.dumps(regions_info, ensure_ascii=False, indent=2),
                current_time=datetime.now().isoformat()
            )
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"构建提示词失败: {e}")
            raise
    
    def _build_summarized_prompt(self, snapshot: DesktopSnapshot, corrections: Dict[str, Any]) -> str:
        """构建摘要版提示词（处理Token限制）"""
        try:
            # 简化的快照数据
            summary = {
                "total_files": snapshot.total_files,
                "main_file_types": dict(list(snapshot.file_type_summary.items())[:5]),
                "key_corrections": dict(list(corrections.items())[:3]) if corrections else {}
            }
            
            simplified_template = """
作为桌面管理AI，请基于以下简化信息生成整理规则：

桌面摘要: {summary}
区域定义: {regions}

请生成JSON格式的规则集，包含version、generated_at、summary、rules和confidence_score字段。
规则应智能分类文件并优化桌面布局。
            """
            
            return simplified_template.format(
                summary=json.dumps(summary, ensure_ascii=False),
                regions=json.dumps(snapshot.regions[:2], ensure_ascii=False)  # 只使用前2个区域
            )
            
        except Exception as e:
            self.logger.error(f"构建摘要提示词失败: {e}")
            raise
    
    def _estimate_tokens(self, text: str) -> int:
        """估算文本的Token数量"""
        # 简单估算：1个Token约等于4个字符
        return len(text) // 4
    
    def _call_llm_with_retry(self, prompt: str, attempt: int) -> Optional[DesktopRuleset]:
        """调用LLM并解析结果"""
        try:
            self.logger.debug(f"LLM调用尝试 {attempt}")
            
            # 发送请求到Gemini
            response = self.model.generate_content(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            if not response or not response.text:
                raise ValueError("LLM返回空响应")
            
            # 解析JSON响应
            response_text = response.text.strip()
            
            # 尝试提取JSON（处理可能的markdown格式）
            json_text = self._extract_json_from_response(response_text)
            
            # 解析并验证JSON
            rule_data = json.loads(json_text)
            
            # 创建Pydantic模型实例
            ruleset = DesktopRuleset(**rule_data)
            
            self.logger.debug("LLM响应解析成功")
            return ruleset
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"LLM调用失败: {e}")
            return None
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """从响应中提取JSON内容"""
        try:
            # 移除markdown代码块标记
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end != -1:
                    return response_text[start:end].strip()
            
            # 尝试查找JSON对象
            start = response_text.find("{")
            if start != -1:
                # 简单的括号匹配
                bracket_count = 0
                for i, char in enumerate(response_text[start:], start):
                    if char == "{":
                        bracket_count += 1
                    elif char == "}":
                        bracket_count -= 1
                        if bracket_count == 0:
                            return response_text[start:i+1]
            
            # 如果都失败，返回原文本
            return response_text
            
        except Exception as e:
            self.logger.warning(f"JSON提取失败: {e}")
            return response_text
    
    def _validate_and_optimize_rules(self, ruleset: DesktopRuleset) -> DesktopRuleset:
        """验证和优化规则集"""
        try:
            # 验证规则的合理性
            valid_rules = []
            
            for rule in ruleset.rules:
                if self._validate_single_rule(rule):
                    valid_rules.append(rule)
                else:
                    self.logger.warning(f"跳过无效规则: {rule.rule_id}")
            
            # 按优先级排序
            valid_rules.sort(key=lambda r: r.priority, reverse=True)
            
            # 去重（基于规则名称）
            seen_names = set()
            deduped_rules = []
            for rule in valid_rules:
                if rule.name not in seen_names:
                    deduped_rules.append(rule)
                    seen_names.add(rule.name)
            
            # 更新规则集
            ruleset.rules = deduped_rules
            
            # 重新计算置信度
            if len(deduped_rules) < len(ruleset.rules):
                ruleset.confidence_score *= 0.9  # 降低置信度
            
            self.logger.info(f"规则验证完成: {len(deduped_rules)}/{len(ruleset.rules)} 有效")
            return ruleset
            
        except Exception as e:
            self.logger.error(f"规则验证失败: {e}")
            return ruleset
    
    def _validate_single_rule(self, rule: IconPlacementRule) -> bool:
        """验证单个规则的有效性"""
        try:
            # 检查必要字段
            if not rule.rule_id or not rule.name:
                return False
            
            # 检查目标区域是否有效
            valid_regions = {"top_left", "top_right", "bottom_left", "bottom_right"}
            if rule.target_region not in valid_regions:
                return False
            
            # 检查优先级范围
            if not 1 <= rule.priority <= 100:
                return False
            
            # 检查条件是否合理
            if not rule.conditions or not isinstance(rule.conditions, dict):
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"规则验证异常: {e}")
            return False
    
    def save_rules_to_file(self, ruleset: DesktopRuleset, filename: Optional[str] = None) -> str:
        """保存规则集到文件"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"rules_{timestamp}.json"
            
            # 确保data目录存在
            data_dir = Path(__file__).parent / "data"
            data_dir.mkdir(exist_ok=True)
            
            filepath = data_dir / filename
            
            # 转换为字典并保存
            rules_dict = ruleset.dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(rules_dict, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"规则集已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"保存规则集失败: {e}")
            raise
    
    def load_rules_from_file(self, filepath: str) -> Optional[DesktopRuleset]:
        """从文件加载规则集"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            ruleset = DesktopRuleset(**data)
            self.logger.info(f"规则集已加载: {filepath}")
            return ruleset
            
        except Exception as e:
            self.logger.error(f"加载规则集失败: {e}")
            return None
        
    def _build_groq_prompt(self, snapshot: DesktopSnapshot, corrections: Dict[str, Any]) -> str:
        """构建Groq AI提示词"""
        try:
            # 准备桌面快照数据
            files = snapshot.files[:20]  # 限制文件数量
            file_types = {}
            for file_info in files:
                ext = getattr(file_info, 'extension', 'unknown')
                file_types[ext] = file_types.get(ext, 0) + 1
            
            # 构建提示词
            prompt = f"""
根据以下桌面文件信息生成智能整理规则：

## 当前桌面状态
- 总文件数: {snapshot.total_files}
- 文件类型分布: {file_types}
- 桌面分辨率: 1920x1080

## 文件详情
{self._format_files_for_groq(files)}

## 用户修正历史
{corrections}

## 要求
请生成JSON格式的整理规则，包含以下结构：
{{
    "regions": {{
        "documents": {{"x_range": [0, 300], "y_range": [0, 200]}},
        "images": {{"x_range": [300, 600], "y_range": [0, 200]}},
        "media": {{"x_range": [600, 900], "y_range": [0, 200]}},
        "archives": {{"x_range": [0, 300], "y_range": [200, 400]}},
        "executables": {{"x_range": [300, 600], "y_range": [200, 400]}},
        "others": {{"x_range": [600, 900], "y_range": [200, 400]}}
    }},
    "rules": [
        {{"pattern": "*.pdf", "target_region": "documents"}},
        {{"pattern": "*.jpg", "target_region": "images"}},
        {{"pattern": "*.mp4", "target_region": "media"}},
        {{"pattern": "*.zip", "target_region": "archives"}},
        {{"pattern": "*.exe", "target_region": "executables"}},
        {{"pattern": "*", "target_region": "others"}}
    ],
    "metadata": {{
        "generated_by": "groq_ai",
        "generation_time": "{datetime.now().isoformat()}",
        "confidence": 0.9
    }}
}}

请确保：
1. 区域不重叠且覆盖整个桌面
2. 规则按照文件类型合理分类
3. 考虑用户的使用习惯

只返回JSON格式的规则，不要包含其他解释文字。
"""
            return prompt
            
        except Exception as e:
            self.logger.error(f"构建Groq提示词失败: {e}")
            return self._get_default_prompt()
    
    def _format_files_for_groq(self, files: List) -> str:
        """格式化文件信息供Groq使用"""
        try:
            formatted_files = []
            for file_info in files[:10]:  # 只显示前10个文件
                filename = getattr(file_info, 'filename', 'unknown')
                extension = getattr(file_info, 'extension', 'unknown')
                size_mb = getattr(file_info, 'size', 0) / (1024 * 1024)
                formatted_files.append(f"- {filename} ({extension}, {size_mb:.1f}MB)")
            
            return "\n".join(formatted_files)
        except Exception:
            return "- 文件信息获取失败"
    
    def _convert_to_pydantic_ruleset(self, rules_dict: Dict) -> Optional[DesktopRuleset]:
        """将字典转换为Pydantic规则集"""
        try:
            # 构建IconPlacementRule列表
            placement_rules = []
            rules = rules_dict.get("rules", [])
            
            for i, rule in enumerate(rules):
                placement_rule = IconPlacementRule(
                    rule_id=f"groq_rule_{i+1:03d}",
                    name=f"规则_{i+1}",
                    description=f"文件模式 {rule.get('pattern', '*')} 移动到 {rule.get('target_region', 'others')}",
                    conditions={"pattern": rule.get("pattern", "*")},
                    target_region=rule.get("target_region", "others"),
                    priority=max(1, 100 - i * 10),  # 优先级递减
                    enabled=True
                )
                placement_rules.append(placement_rule)
            
            # 创建DesktopRuleset
            ruleset = DesktopRuleset(
                version="1.0",
                generated_at=datetime.now().isoformat(),
                summary=f"Groq AI生成的智能整理规则 - {len(placement_rules)}条规则",
                rules=placement_rules,
                confidence_score=rules_dict.get("metadata", {}).get("confidence", 0.8)
            )
            
            return ruleset
            
        except Exception as e:
            self.logger.error(f"转换Pydantic规则集失败: {e}")
            return None
    
    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return """
生成桌面文件整理规则：

请生成JSON格式规则：
{
    "regions": {
        "documents": {"x_range": [0, 300], "y_range": [0, 200]},
        "others": {"x_range": [300, 600], "y_range": [0, 200]}
    },
    "rules": [
        {"pattern": "*.pdf", "target_region": "documents"},
        {"pattern": "*", "target_region": "others"}
    ]
}
"""

# ==================== 全局实例和便捷函数 ====================

_strategy_engine_instance: Optional[AIStrategyEngine] = None


def get_strategy_engine() -> AIStrategyEngine:
    """获取全局策略引擎实例"""
    global _strategy_engine_instance
    if _strategy_engine_instance is None:
        _strategy_engine_instance = AIStrategyEngine()
    return _strategy_engine_instance


def generate_smart_rules(snapshot: DesktopSnapshot, corrections: Dict[str, Any] = None) -> Optional[DesktopRuleset]:
    """生成智能整理规则"""
    if corrections is None:
        corrections = {}
    return get_strategy_engine().generate_rules_from_llm(snapshot, corrections)


if __name__ == "__main__":
    # 测试代码
    print("=== Aether Desktop AI策略引擎测试 ===")
    
    try:
        # 注意：需要在config.ini中配置有效的API密钥才能运行测试
        print("\n测试需要有效的Gemini API密钥")
        print("请在config.ini中配置 gemini_api_key")
        
        # engine = get_strategy_engine()
        # print("AI策略引擎初始化成功")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
