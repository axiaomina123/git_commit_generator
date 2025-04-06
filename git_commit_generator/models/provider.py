import json
import os
from typing import Dict, Any, List
from requests import api


class Provider:
    """统一的Provider类，能够适配各种大模型API"""
    
    def __init__(self):
        from git_commit_generator.config import ConfigManager
        self.config = ConfigManager()._load_config()
        self.current_provider = self.config.get('current_provider', '')
        providers = self.config.get('providers', {})
        self.max_tokens = providers.get(self.current_provider, {}).get('max_tokens', 1024)
        self.api_key = providers.get(self.current_provider, {}).get('api_key', '')
        self.model_name = providers.get(self.current_provider, {}).get('model_name', '')
        self.model_url = providers.get(self.current_provider, {}).get('model_url', '')
        self.provider_type = self._get_provider_type()
        
        
    def _read_provider_file(self, error_message: str) -> Dict[str, Any]:
        """读取提供商配置文件"""
        try:
            file_path = os.path.join(os.path.dirname(__file__), '.provider.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            raise FileNotFoundError(error_message)

    def _get_provider_type(self) -> str:
        """根据提供商名称获取提供商类型"""
        json_file_providers = self._read_provider_file("无法加载提供商类型")
        provider_info = json_file_providers.get(self.current_provider, {})
        return provider_info.get('provider', 'OtherProvider')

    def _write_provider_file(self, data: Dict[str, Any], error_message: str) -> None:
        """写入提供商配置文件"""
        try:
            file_path = os.path.join(os.path.dirname(__file__), '.provider.json')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except (FileNotFoundError, PermissionError) as e:
            raise IOError(f"{error_message}: {str(e)}")

    def get_providers(self) -> List[str]:
        """获取所有模型提供商"""
        providers = self._read_provider_file("模型加载失败")
        return list(providers.keys())

    def get_model_name(self, provider_name: str) -> str:
        """获取指定提供商的模型名称"""
        providers = self._read_provider_file("无法加载模型名称")
        return providers.get(provider_name, {}).get('model_name', '')

    def get_model_url(self, provider_name: str) -> str:
        """获取指定提供商的模型URL"""
        providers = self._read_provider_file("无法加载模型URL")
        return providers.get(provider_name, {}).get('model_url', '')
    
    def _prepare_headers(self) -> Dict[str, str]:
        """根据不同提供商准备请求头"""
        headers = {"Content-Type": "application/json"}
        
        if self.provider_type == "AzureProvider":
            headers["api-key"] = self.api_key
        else:  # 大多数API使用Bearer认证
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers
    
    def _prepare_data(self, prompt: str) -> Dict[str, Any]:
        """根据不同提供商准备请求数据"""
        if self.provider_type == "HuggingFaceProvider":
            return {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": self.max_tokens,
                    "temperature": 0.7
                }
            }
        elif self.provider_type == "GoogleProvider":
            return {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
        elif self.provider_type == "ChatGLMProvider":
            return {
                "model": self.model_name,
                "prompt": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": self.max_tokens
            }
        elif self.provider_type in ["DeepseekProvider", "OtherProvider"]:
            return {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "max_tokens": self.max_tokens,
                "stop": None,
                "temperature": 0.7,
                "top_p": 0.7,
                "top_k": 50,
                "frequency_penalty": 0.5,
                "n": 1
            }
        else:  # OpenAI和Azure等使用类似格式
            return {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": self.max_tokens
            }
    
    def _prepare_url(self) -> str:
        """根据不同提供商准备请求URL"""
        if self.provider_type == "AzureProvider":
            return f"{self.model_url}?api-version=2023-05-15"
        return self.model_url
    
    def _parse_response(self, response_json: Dict[str, Any]) -> str:
        """根据不同提供商解析响应"""
        if self.provider_type == "HuggingFaceProvider":
            return response_json['generated_text'].strip()
        elif self.provider_type == "GoogleProvider":
            return response_json['candidates'][0]['content']['parts'][0]['text'].strip()
        else:  # OpenAI, Azure, DeepSeek, ChatGLM等使用类似格式
            return response_json['choices'][0]['message']['content'].strip()
    
    def _get_error_message(self) -> str:
        """获取错误信息前缀"""
        provider_error_messages = {
            "OpenaiProvider": "OpenAI API请求失败",
            "AzureProvider": "Azure API请求失败",
            "HuggingFaceProvider": "HuggingFace API请求失败",
            "DeepseekProvider": "DeepSeek API请求失败",
            "GoogleProvider": "Google API请求失败",
            "ChatGLMProvider": "ChatGLM API请求失败",
            "OtherProvider": "API请求失败"
        }
        return provider_error_messages.get(self.provider_type, "API请求失败")

    def generate(self, prompt: str) -> str:
        """统一的生成接口，适配各种大模型API"""
        headers = self._prepare_headers()
        data = self._prepare_data(prompt)
        url = self._prepare_url()
        
        try:
            # 对于DeepSeek等可能需要调试的提供商，保留调试信息
            if self.provider_type in ["DeepseekProvider", "OtherProvider"]:
                print(self.model_name, url)
                
            response = api.post(url, headers=headers, json=data)
            response.raise_for_status()
            return self._parse_response(response.json())
        except Exception as e:
            error_message = self._get_error_message()
            raise Exception(f"{error_message}: {str(e)}")

# 为了向后兼容，保留原有类名
class BaseProvider(Provider):
    """为了向后兼容而保留的基类"""
    pass

class OpenaiProvider(Provider):
    """为了向后兼容而保留的OpenAI提供商类"""
    def __init__(self):
        super().__init__()
        self.provider_type = "OpenaiProvider"

class AzureProvider(Provider):
    """为了向后兼容而保留的Azure提供商类"""
    def __init__(self):
        super().__init__()
        self.provider_type = "AzureProvider"

class HuggingFaceProvider(Provider):
    """为了向后兼容而保留的HuggingFace提供商类"""
    def __init__(self):
        super().__init__()
        self.provider_type = "HuggingFaceProvider"

class DeepseekProvider(Provider):
    """为了向后兼容而保留的DeepSeek提供商类"""
    def __init__(self):
        super().__init__()
        self.provider_type = "DeepseekProvider"

class GoogleProvider(Provider):
    """为了向后兼容而保留的Google提供商类"""
    def __init__(self):
        super().__init__()
        self.provider_type = "GoogleProvider"

class ChatGLMProvider(Provider):
    """为了向后兼容而保留的ChatGLM提供商类"""
    def __init__(self):
        super().__init__()
        self.provider_type = "ChatGLMProvider"

class OtherProvider(Provider):
    """为了向后兼容而保留的其他提供商类"""
    def __init__(self):
        super().__init__()
        self.provider_type = "OtherProvider"
