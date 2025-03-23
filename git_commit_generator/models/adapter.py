from .provider import *
import importlib

class ModelAdapter:
    def __init__(self, provider_name: str):
        providers = BaseProvider()._read_provider_file("配置加载失败")
        provider_class = providers.get(provider_name, {})['provider'] if provider_name in providers.keys() else "OtherProvider"
        module = importlib.import_module('git_commit_generator.models.provider')
        self.provider_instance = getattr(module, provider_class)()
        self.provider_name = provider_name

    def generate_commit(self, diff: str) -> str:
        return self.provider_instance.generate(diff)

    def generate(self, prompt: str) -> str:
        """统一生成接口"""
        return self.provider_instance.generate(prompt)