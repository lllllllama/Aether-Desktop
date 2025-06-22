"""
AI服务提供商管理器 - 支持Groq免费API
===================================
"""

import json
import requests
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime

from .logger import get_logger
from .config_manager import get_config


class AIProvider(ABC):
    """AI服务提供商基类"""
    
    @abstractmethod
    def generate_rules(self, prompt: str, schema: Dict) -> Dict:
        pass


class GroqProvider(AIProvider):
    """Groq API提供商 - 免费且高速"""
    
    def __init__(self, api_key: str, model: str = "llama3-8b-8192"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1"
        self.logger = get_logger(__name__)
    
    def generate_rules(self, prompt: str, schema: Dict = None) -> Dict:
        """使用Groq API生成整理规则"""
        try:
            self.logger.info(f"正在调用Groq API生成规则...")
            
            # 构建请求
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个桌面文件整理专家。请根据用户的桌面文件信息，生成JSON格式的整理规则。只返回JSON，不要包含任何解释文字。"
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1024
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # 提取JSON内容
                if "```json" in content:
                    # 从markdown代码块中提取JSON
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    json_str = content[start:end].strip()
                elif "```" in content:
                    # 从普通代码块中提取JSON
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    json_str = content[start:end].strip()
                else:
                    json_str = content.strip()
                
                try:
                    rules = json.loads(json_str)
                    self.logger.info("Groq API调用成功，规则生成完毕")
                    return rules
                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON解析失败: {e}, 使用降级规则")
                    return self._get_fallback_rules()
            else:
                self.logger.error(f"Groq API错误: {response.status_code} - {response.text}")
                return self._get_fallback_rules()
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Groq网络请求失败: {e}")
            return self._get_fallback_rules()
        except Exception as e:
            self.logger.error(f"Groq调用异常: {e}")
            return self._get_fallback_rules()
    
    def _get_fallback_rules(self) -> Dict:
        """降级规则 - 当API调用失败时使用"""
        return {
            "regions": {
                "documents": {"x_range": [0, 300], "y_range": [0, 200]},
                "images": {"x_range": [300, 600], "y_range": [0, 200]},
                "media": {"x_range": [600, 900], "y_range": [0, 200]},
                "archives": {"x_range": [0, 300], "y_range": [200, 400]},
                "executables": {"x_range": [300, 600], "y_range": [200, 400]},
                "others": {"x_range": [600, 900], "y_range": [200, 400]}
            },
            "rules": [
                {"pattern": "*.pdf", "target_region": "documents"},
                {"pattern": "*.doc*", "target_region": "documents"},
                {"pattern": "*.txt", "target_region": "documents"},
                {"pattern": "*.jpg", "target_region": "images"},
                {"pattern": "*.png", "target_region": "images"},
                {"pattern": "*.gif", "target_region": "images"},
                {"pattern": "*.mp4", "target_region": "media"},
                {"pattern": "*.mp3", "target_region": "media"},
                {"pattern": "*.zip", "target_region": "archives"},
                {"pattern": "*.rar", "target_region": "archives"},
                {"pattern": "*.exe", "target_region": "executables"},
                {"pattern": "*.msi", "target_region": "executables"},
                {"pattern": "*", "target_region": "others"}
            ],
            "metadata": {
                "generated_by": "fallback_system",
                "generation_time": datetime.now().isoformat(),
                "confidence": 0.7
            }
        }


class OpenRouterProvider(AIProvider):
    """OpenRouter API提供商 - 支持多种模型的聚合服务"""
    
    def __init__(self, api_key: str, model: str = "meta-llama/llama-3.1-8b-instruct:free"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.logger = get_logger(__name__)
    
    def generate_rules(self, prompt: str, schema: Dict = None) -> Dict:
        """使用OpenRouter API生成整理规则"""
        try:
            self.logger.info(f"正在调用OpenRouter API生成规则... 模型: {self.model}")
            
            # 构建请求
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://aether-desktop.com",  # 可选，用于统计
                    "X-Title": "Aether Desktop"  # 可选，应用标识
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个桌面文件整理专家。请根据用户的桌面文件信息，生成JSON格式的整理规则。只返回JSON，不要包含任何解释文字。"
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1024,
                    "top_p": 1,
                    "frequency_penalty": 0,
                    "presence_penalty": 0
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # 提取JSON内容
                if "```json" in content:
                    # 从markdown代码块中提取JSON
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    json_str = content[start:end].strip()
                elif "```" in content:
                    # 从普通代码块中提取JSON
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    json_str = content[start:end].strip()
                else:
                    json_str = content.strip()
                
                try:
                    rules = json.loads(json_str)
                    self.logger.info("OpenRouter API调用成功，规则生成完毕")
                    return rules
                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON解析失败: {e}, 使用降级规则")
                    return self._get_fallback_rules()
            else:
                self.logger.error(f"OpenRouter API错误: {response.status_code} - {response.text}")
                return self._get_fallback_rules()
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"OpenRouter网络请求失败: {e}")
            return self._get_fallback_rules()
        except Exception as e:
            self.logger.error(f"OpenRouter调用异常: {e}")
            return self._get_fallback_rules()
    
    def _get_fallback_rules(self) -> Dict:
        """降级规则 - 当API调用失败时使用"""
        return {
            "regions": {
                "documents": {"x_range": [0, 300], "y_range": [0, 200]},
                "images": {"x_range": [300, 600], "y_range": [0, 200]},
                "media": {"x_range": [600, 900], "y_range": [0, 200]},
                "archives": {"x_range": [0, 300], "y_range": [200, 400]},
                "executables": {"x_range": [300, 600], "y_range": [200, 400]},
                "others": {"x_range": [600, 900], "y_range": [200, 400]}
            },
            "rules": [
                {"pattern": "*.pdf", "target_region": "documents"},
                {"pattern": "*.doc*", "target_region": "documents"},
                {"pattern": "*.txt", "target_region": "documents"},
                {"pattern": "*.jpg", "target_region": "images"},
                {"pattern": "*.png", "target_region": "images"},
                {"pattern": "*.gif", "target_region": "images"},
                {"pattern": "*.mp4", "target_region": "media"},
                {"pattern": "*.mp3", "target_region": "media"},
                {"pattern": "*.zip", "target_region": "archives"},
                {"pattern": "*.rar", "target_region": "archives"},
                {"pattern": "*.exe", "target_region": "executables"},
                {"pattern": "*.msi", "target_region": "executables"},
                {"pattern": "*", "target_region": "others"}
            ],
            "metadata": {
                "generated_by": "openrouter_fallback",
                "generation_time": datetime.now().isoformat(),
                "confidence": 0.7
            }
        }


class AIProviderManager:
    """AI服务提供商管理器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.current_provider = None
        self.providers = {}
        self._setup_providers()
    
    def _setup_providers(self):
        """设置AI提供商"""
        try:
            # 1. OpenRouter (优先级最高 - 支持多种免费模型)
            openrouter_api_key = self.config.get("AI_CONFIG", "openrouter_api_key", fallback="").strip()
            if openrouter_api_key:
                openrouter_model = self.config.get("AI_CONFIG", "openrouter_model", fallback="meta-llama/llama-3.1-8b-instruct:free")
                self.providers["openrouter"] = OpenRouterProvider(openrouter_api_key, openrouter_model)
                self.logger.info(f"注册OpenRouter提供商: {openrouter_model}")
            
            # 2. Groq (高速免费)
            groq_api_key = self.config.get("AI_CONFIG", "groq_api_key", fallback="").strip()
            if groq_api_key:
                groq_model = self.config.get("AI_CONFIG", "groq_model", fallback="llama3-8b-8192")
                self.providers["groq"] = GroqProvider(groq_api_key, groq_model)
                self.logger.info(f"注册Groq提供商: {groq_model}")
            
            # 选择当前提供商 (按优先级)
            provider_priority = ["openrouter", "groq"]
            current_provider_config = self.config.get("AI_CONFIG", "current_provider", fallback="auto").strip()
            
            if current_provider_config != "auto" and current_provider_config in self.providers:
                # 用户指定了特定提供商
                self.current_provider = self.providers[current_provider_config]
                self.logger.info(f"使用指定的AI提供商: {current_provider_config}")
            else:
                # 自动选择第一个可用的提供商
                for provider_name in provider_priority:
                    if provider_name in self.providers:
                        self.current_provider = self.providers[provider_name]
                        self.logger.info(f"自动选择AI提供商: {provider_name}")
                        break
            
            if not self.current_provider:
                self.logger.warning("未配置任何AI提供商，将使用降级规则")
                
        except Exception as e:
            self.logger.error(f"AI提供商初始化失败: {e}")
            self.current_provider = None
    
    def get_available_providers(self) -> List[str]:
        """获取可用的提供商列表"""
        return list(self.providers.keys())
    
    def switch_provider(self, provider_name: str) -> bool:
        """切换AI提供商"""
        if provider_name in self.providers:
            self.current_provider = self.providers[provider_name]
            self.logger.info(f"切换到AI提供商: {provider_name}")
            return True
        else:
            self.logger.warning(f"未找到AI提供商: {provider_name}")
            return False
    
    def get_current_provider_info(self) -> Dict[str, str]:
        """获取当前提供商信息"""
        if self.current_provider:
            provider_name = None
            for name, provider in self.providers.items():
                if provider == self.current_provider:
                    provider_name = name
                    break
            
            if isinstance(self.current_provider, OpenRouterProvider):
                return {
                    "name": "OpenRouter",
                    "model": self.current_provider.model,
                    "type": "openrouter"
                }
            elif isinstance(self.current_provider, GroqProvider):
                return {
                    "name": "Groq",
                    "model": self.current_provider.model,
                    "type": "groq"
                }
        
        return {"name": "None", "model": "fallback", "type": "fallback"}
    
    def generate_rules(self, prompt: str, schema: Dict = None) -> Dict:
        """生成整理规则"""
        if self.current_provider:
            provider_info = self.get_current_provider_info()
            self.logger.info(f"使用 {provider_info['name']} ({provider_info['model']}) 生成规则")
            return self.current_provider.generate_rules(prompt, schema or {})
        else:
            self.logger.warning("没有可用的AI提供商，使用默认规则")
            dummy_provider = GroqProvider("dummy_key")
            return dummy_provider._get_fallback_rules()


# 创建全局AI管理器实例
ai_manager = AIProviderManager()
