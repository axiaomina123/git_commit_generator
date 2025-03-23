from urllib.parse import urlparse
from typing import Any
import requests

class FieldValidator:
    @classmethod
    def validate(cls, value: Any) -> Any:
        raise NotImplementedError

class ProviderValidator(FieldValidator):
    @classmethod
    def validate(cls, value: str) -> str:
        if not value.isidentifier() or '-' in value:
            raise ValueError("提供商名称必须符合Python标识符规范且不包含连字符")
        return value

class UrlValidator(FieldValidator):
    @classmethod
    def validate(cls, value: str) -> str:
        result = urlparse(value)
        if not all([result.scheme, result.netloc]):
            raise ValueError("无效的URL格式，必须包含协议和域名")
        
        # 可选连通性检查（根据性能需求决定是否启用）
        try:
            resp = requests.head(value, timeout=3)
            if resp.status_code >= 400:
                raise ValueError(f"URL无法访问，状态码：{resp.status_code}")
        except requests.RequestException:
            pass
            
        return value

class ApiKeyValidator(FieldValidator):
    @classmethod
    def validate(cls, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError("API秘钥必须为字符串类型")
        if not value.strip():
            raise ValueError("API秘钥不能为空")
        return value

class MaxTokensValidator(FieldValidator):
    @classmethod
    def validate(cls, value: int) -> int:
        if not isinstance(value, int):
            raise TypeError("max_tokens必须为整型")
        if value < 100 or value > 4096:
            raise ValueError("max_tokens需在100-4096范围内")
        return value

class ModelNameValidator(FieldValidator):
    @classmethod
    def validate(cls, value: str) -> str:
        return value.strip()  # 允许空值，自动去除前后空格

class FieldValidatorFactory:
    _validators = {
        'current_provider': ProviderValidator,
        'model_url': UrlValidator,
        'api_key': ApiKeyValidator,
        'max_tokens': MaxTokensValidator,
        'model_name': ModelNameValidator
    }

    @classmethod
    def get_validator(cls, key: str) -> FieldValidator:
        validator = cls._validators.get(key)
        if not validator:
            raise ValueError(f"未找到{key}的验证器")
        return validator()