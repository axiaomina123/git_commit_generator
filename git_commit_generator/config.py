from re import T
import re
from typing import Callable, Union
import json
import os

from click.core import F
import typer
from questionary import confirm, select

from .models.provider import Provider



class ConfigManager:
    def __init__(self):
        config_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.config_file = os.path.join(config_dir, '.config.json')
        # 自动创建配置目录
        os.makedirs(config_dir, exist_ok=True)
        
    def _mask_api_key(self, api_key: str) -> str:
        """对API密钥进行掩码处理，只显示前4位和后4位"""
        if not api_key or len(api_key) < 8:
            return "****" if api_key else ""
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]

    def _handle_file_operation(self, file_path: str, mode: str, success_handler: Callable, error_prefix: str):
        """文件操作统一处理"""
        try:
            with open(file_path, mode, encoding='utf-8') as f:
                return success_handler(f)
        except Exception as e:
            return {}

    def _load_config(self) -> dict:
        """加载配置文件统一入口"""
        return self._handle_file_operation(
            file_path=self.config_file,
            mode='r',
            success_handler=lambda f: json.load(f) if os.path.exists(self.config_file) else {},
            error_prefix='读取配置'
        )

    def _save_config(self, config: dict):
        """保存配置统一入口"""
        self._handle_file_operation(
            file_path=self.config_file,
            mode='w',
            success_handler=lambda f: json.dump(config, f, indent=4, ensure_ascii=False),
            error_prefix='保存配置'
        )

    def _validate_input(self, key: str, value: Union[str, int]):
        """
        统一输入验证逻辑
        :param key: 配置项名称       
        :param value: 配置项值
        """
        from .validators import FieldValidatorFactory
        validator = FieldValidatorFactory.get_validator(key)
        validated_value = validator.validate(value)
        # 保留原有配置项白名单检查
        if key not in ['current_provider', 'model_name', 'model_url', 'api_key', 'max_tokens']:
            return False, f"无效的配置项: {key}"
        return True, validated_value


    def get(self, key: str, provider_name: Union[str, None] = None, mask_api_key: bool = True):
        """获取配置值
        :param provider_name: 指定模型提供商名称，为空时获取全局配置
        :param mask_api_key: 是否对API密钥进行掩码处理
        """
        config = self._load_config()
        value = ""
        if provider_name:
            if key:
                value = config.get('providers', {}).get(provider_name, {}).get(key, 1024 if key == 'max_tokens' else "")
            else:
                value = config.get('providers', {}).get(provider_name, {})
                value['api_key'] = self._mask_api_key(value['api_key']) if value['api_key'] else value['api_key']
        else:
            value = config.get(key, '不存在的全局配置项')
            
        # 对API密钥进行掩码处理
        if key == 'api_key' and mask_api_key and value:
            return True, self._mask_api_key(value)
        return True, value
    

    def config_list(self, mask_api_key: bool = True):
        """列出所有配置
        :param mask_api_key: 是否对API密钥进行掩码处理
        """
        self._config = self._load_config()
        if not self._config:
            return False, "尚未添加模型，请先用 newpro 命令添加"
            
        # 创建配置的副本，以便不修改原始配置
        config_copy = json.loads(json.dumps(self._config))
        
        # 对API密钥进行掩码处理
        if mask_api_key and 'providers' in config_copy:
            for provider, provider_config in config_copy['providers'].items():
                if 'api_key' in provider_config and provider_config['api_key']:
                    provider_config['api_key'] = self._mask_api_key(provider_config['api_key'])
        
        return True, config_copy
        

    def config_set(self, key: str, value: Union[str, int], provider_name: Union[str, None] = None):
        """设置配置值
        :param provider_name: 指定模型提供商名称
        """
        # 输入参数验证
        try:
            self._validate_input(key, value)
        except Exception as e:
            return False, f"{key}输入错误:{str(e)}，设置失败"
        
        self._config = self._load_config()
        if 'providers' not in self._config:
            return False, "尚未添加模型，请先用 newpro 命令添加"
        # 更新逻辑
        if provider_name:
            # 存在性校验
            if provider_name not in self._config['providers']:
                return False, f"模型提供商 {provider_name} 不存在"
            # 更新指定提供商的配置
            self._config['providers'][provider_name][key] = value
            return_value = f"已成功更新 {provider_name} 的 {key} 配置"
        else:
            # 更新全局配置
            if key == 'current_provider' and value not in self._config['providers']:
                return False, f"模型提供商 {value} 不存在"
            self._config[key] = value
            return_value = f"已成功更新 {key} 配置"
        self._save_config(self._config)
        return True, return_value

    def _retry_or_pass(self, key, zh_key, default_value=None):
        """与用户交互 用户输入内容不合法重试"""
        while True:
            if default_value:
                value = typer.prompt(f"请输入{zh_key}：", default=default_value)
            else:
                value = typer.prompt(f"请输入{zh_key}：")
            try:
                self._validate_input(key, value)
                break
            except Exception as e:
                typer.echo(f"{key}输入错误:{str(e)}，请重新输入")
                break
        return value

    def config_newpro(self):
        """新增模型配置"""
        base_provider = Provider()
        providers = base_provider.get_providers()
        choices = [
            {"name": f"{provider}", "value": provider}
            for provider in providers
        ]
        choices.append({"name": "手动输入", "value": "manual"})
        
        selected = select(
            "请选择模型提供商:",
            choices=choices,
            use_arrow_keys=True
        ).ask()
        if not selected:
            return False, "未选择任何模型提供商"
        # 用户选择手动输入时，需要手动输入模型提供商，模型URL和模型名称
        if selected == "manual":
            current_provider = self._retry_or_pass('current_provider', '模型提供商名称')
            model_url = self._retry_or_pass('model_url', '模型URL')
            model_name = self._retry_or_pass('model_name', '模型名称')
        else:
            # 自动获取默认模型提供商，模型名称和URL
            current_provider = self._retry_or_pass('current_provider', '模型提供商名称', selected)
            default_model_name= base_provider.get_model_name(current_provider)
            default_model_url= base_provider.get_model_url(current_provider)
            model_url = self._retry_or_pass('model_url', '模型URL', default_model_url)
            model_name = self._retry_or_pass('model_name', '模型名称', default_model_name)
        # 新增max_tokens输入，带默认值
        max_tokens = self._retry_or_pass('max_tokens', '最大token数', 1024)
        # API密钥必填校验
        api_key = self._retry_or_pass('api_key', 'API密钥')

        self._pending_config = self._load_config()
        # 初始化providers结构
        if 'providers' not in self._pending_config:
            self._pending_config['providers'] = {}
        # 添加新的模型配置 
        self._pending_config['providers'][current_provider] = {
            'model_url': model_url,
            'model_name': model_name,
            'max_tokens': max_tokens,
            'api_key': api_key
        }
        # 更新全局配置
        self._pending_config['current_provider'] = current_provider
        self._save_config(self._pending_config)
        return True, "模型配置已成功添加"

    def select_model(self):
        """
        交互式选择当前使用模型
        """
        try:
            self._config = self._load_config()

            if not self._config.get('providers'):
                return False, "当前没有可用的模型配置"

            providers = list(self._config['providers'].keys())
            choices = [
                {"name": f"{p}（当前使用）", "value": p}
                if p == self._config.get('current_provider')
                else {"name": p, "value": p}
                for p in providers
            ]

            selected = select(
                "请选择要使用的模型提供商：",
                choices=choices,
            ).ask()
            if not selected:
                return False, "未选择任何模型提供商"

            provider = selected

            self._config['current_provider'] = provider
            self._save_config(self._config)
            return True, provider
        except KeyboardInterrupt:
            # 用户强制退出时不做任何操作
            return False, "已取消操作"

    def config_remove(self, provider_name: Union[str, None] = None, all_flag: bool = False):
        """移除指定或全部模型配置"""
        
        self._config = self._load_config()

        if not self._config.get('providers'):
            return False, "当前没有可用的模型配置"

        # 处理全部删除
        if all_flag:
            confirmed = confirm("确定要删除所有模型配置吗？此操作不可恢复！").ask()
            if not confirmed:
                return  False, "已取消删除操作"  
            self._config['providers'] = {}
            self._config.pop('current_provider', None)
            self._save_config(self._config)
            return True, "已移除所有模型配置"

        # 处理单个删除
        if not provider_name:
            return False, "未指定要删除的模型提供商"

        if provider_name not in self._config['providers']:
            return False, f"模型提供商 {provider_name} 不存在" 

        # 删除当前使用模型时的处理
        if provider_name == self._config.get('current_provider'):
            typer.echo("正在删除当前使用的模型，需要先切换模型")
            self.select_model()
            self._config = self._load_config()

        confirmed = confirm(f"确定要删除 {provider_name} 的配置吗？").ask()
        if not confirmed:
            return False, "已取消删除操作"

        del self._config['providers'][provider_name]
        # 如果删除的是当前模型且没有切换，清空current_provider
        if provider_name == self._config.get('current_provider'):
            self._config['current_provider'] = None
        self._save_config(self._config)
        return True, f"已成功移除 {provider_name} 的配置"

    def config_reset(self):
        """重置配置"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            self._config = {}
            return True, "配置已重置"
        except Exception as e:
            return False, f"重置配置失败: {str(e)}"