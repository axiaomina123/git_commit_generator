import json
import os

from requests import api
class BaseProvider:
    def __init__(self):
        from git_commit_generator.config import ConfigManager
        self.config = ConfigManager()._load_config()
        self.current_provider = self.config.get('current_provider')
        providers = self.config.get('providers', {})
        self.max_tokens = providers.get(self.current_provider, {}).get('max_tokens', 1024)
        self.api_key = providers.get(self.current_provider, {}).get('api_key', '')
        self.model_name = providers.get(self.current_provider, {}).get('model_name', '')
        self.model_url = providers.get(self.current_provider, {}).get('model_url', '')
        
    # 获取所有模型提供商
    def _read_provider_file(self, error_message):
        try:
            file_path = os.path.join(os.path.dirname(__file__), '.provider.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            raise FileNotFoundError(error_message)

    def _write_provider_file(self, data, error_message):
        try:
            file_path = os.path.join(os.path.dirname(__file__), '.provider.json')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except (FileNotFoundError, PermissionError) as e:
            raise IOError(f"{error_message}: {str(e)}")

    def get_providers(self) -> list:
        """
        获取所有模型提供商
        :return: 模型提供商列表
        """
        providers = self._read_provider_file("模型加载失败")
        return list(providers.keys())

    def get_model_name(self, provider_name: str) -> str:
        """
        获取指定提供商的模型名称
        :param provider_name: 提供商名称
        :return: 模型名称
        """
        providers = self._read_provider_file("无法加载模型名称")
        return providers.get(provider_name, {}).get('model_name', '')

    def get_model_url(self, provider_name: str) -> str:
        """
        获取指定提供商的模型URL
        :param provider_name: 提供商名称
        :return: 模型URL
        """
        providers = self._read_provider_file("无法加载模型URL")
        return providers.get(provider_name, {}).get('model_url', '')


class OpenaiProvider(BaseProvider):
    def __init__(self):
        super().__init__()

    def generate(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": self.max_tokens
        }
        
        try:
            response = api.post(self.model_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            raise Exception(f"OpenAI API请求失败: {str(e)}")

class AzureProvider(BaseProvider):
    def __init__(self):
        super().__init__()

    def generate(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": self.max_tokens
        }

        try:
            response = api.post(f"{self.model_url}?api-version=2023-05-15", 
                              headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            raise Exception(f"Azure API请求失败: {str(e)}")

class HuggingFaceProvider(BaseProvider):
    def __init__(self):
        super().__init__()

    def generate(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": self.max_tokens,
                "temperature": 0.7
            }
        }

        try:
            response = api.post(self.model_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()[0]['generated_text'].strip()
        except Exception as e:
            raise Exception(f"HuggingFace API请求失败: {str(e)}")

class DeepseekProvider(BaseProvider):
    def __init__(self):
        super().__init__()

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
            "max_tokens": self.max_tokens,
            "stop": None,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            # "response_format": {"type": "text"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            print(self.model_name, self.model_url)
            response = api.post(self.model_url, headers=headers, json=payload)
            # print(response.json())
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            raise Exception(f"DeepSeek API请求失败: {str(e)}")

class GoogleProvider(BaseProvider):
    def __init__(self):
        super().__init__()

    def generate(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        try:
            response = api.post(self.model_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception as e:
            raise Exception(f"Google API请求失败: {str(e)}")

class ChatGLMProvider(BaseProvider):
    def __init__(self):
        super().__init__()

    def generate(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.model_name,
            "prompt": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": self.max_tokens
        }

        try:
            response = api.post(self.model_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            raise Exception(f"ChatGLM API请求失败: {str(e)}")

class OtherProvider(BaseProvider):
    def __init__(self):
        super().__init__()

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
            "max_tokens": self.max_tokens,
            "stop": None,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            # "response_format": {"type": "text"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            print(self.model_name, self.model_url)
            response = api.post(self.model_url, headers=headers, json=payload)
            # print(response.json())
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            raise Exception(f"DeepSeek API请求失败: {str(e)}")
