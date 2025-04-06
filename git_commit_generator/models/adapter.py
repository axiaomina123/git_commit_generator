from .provider import Provider

class ModelAdapter:
    def __init__(self, provider_name: str):
        self.provider_instance = Provider()
        self.provider_instance.current_provider = provider_name
        # 重新初始化Provider实例的配置
        from git_commit_generator.config import ConfigManager
        config = ConfigManager()._load_config()
        providers = config.get('providers', {})
        self.provider_instance.max_tokens = providers.get(provider_name, {}).get('max_tokens', 1024)
        self.provider_instance.api_key = providers.get(provider_name, {}).get('api_key', '')
        self.provider_instance.model_name = providers.get(provider_name, {}).get('model_name', '')
        self.provider_instance.model_url = providers.get(provider_name, {}).get('model_url', '')
        self.provider_instance.provider_type = self.provider_instance._get_provider_type()
        self.provider_name = provider_name

    def generate_commit(self, diff: str) -> str:
        """生成提交信息"""
        return self.provider_instance.generate(diff)

    def generate(self, prompt: str) -> str:
        """统一生成接口"""
        return self.provider_instance.generate(prompt)