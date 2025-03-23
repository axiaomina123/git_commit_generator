from typing import Callable
import json
import os
import typer

from .models.provider import BaseProvider



class ConfigManager:
    def __init__(self):
        config_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.config_file = os.path.join(config_dir, '.config.json')
        # 自动创建配置目录
        os.makedirs(config_dir, exist_ok=True)

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

    def _validate_input(self, key: str, value: str | int):
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
            raise ValueError(f"无效的配置项: {key}")
        return validated_value


    def get(self, key: str, provider_name: str | None = None):
        """获取配置值
        :param provider_name: 指定模型提供商名称，为空时获取全局配置
        """
        config = self._load_config()
        if provider_name:
            return config.get('providers', {}).get(provider_name, {}).get(key, 1024 if key == 'max_tokens' else "")
        return config.get(key, 1024 if key == 'max_tokens' else "")
    

    def list(self):
        """列出所有配置"""
        self._config = self._load_config()
        return self._config if self._config else {}
        

    def set(self, key: str, value: str | int, provider_name: str | None = None):
        """设置配置值
        :param provider_name: 指定模型提供商名称
        """
        # 输入参数验证
        try:
            self._validate_input(key, value)
        except Exception as e:
            typer.echo(f"{key}输入错误:{str(e)}，设置失败")
            exit(1)
        self._config = self._load_config()
        if 'providers' not in self._config:
            raise typer.Abort("尚未添加模型，请先用 newpro 命令添加")
        # 更新逻辑
        if provider_name:
            # 存在性校验
            if provider_name not in self._config.get('providers', {}):
                raise typer.Abort("尚未添加指定的提供商模型，请先用 newpro 命令添加")
            # 更新指定提供商的配置
            self._config['providers'][provider_name][key] = value
        else:
            # 更新全局配置
            self._config[key] = value
        self._save_config(self._config)

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
                typer.echo(f"{zh_key}输入错误:{str(e)}，请重新输入")
        return value

    def newpro(self):
        """新增模型配置"""
        from questionary import select
        base_provider = BaseProvider()
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
            typer.echo("未选择任何模型提供商")
            return
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
        typer.echo("模型配置已成功添加,并已切换到当前模型")

    def select_model(self, provider_name: str | None = None):
        """
        交互式选择当前使用模型
        """
        from questionary import select
        self._config = self._load_config()

        if not self._config.get('providers'):
            raise typer.Abort("当前没有可用的模型配置，请先使用 newpro 命令添加")

        if provider_name:
            if provider_name not in self._config['providers']:
                raise typer.Abort(f"提供商 {provider_name} 不存在")
            self._config['current_provider'] = provider_name
            self._save_config(self._config)
            typer.echo(f"已切换到模型提供商：{provider_name}")
        else:
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
                use_arrow_keys=True
            ).ask()

            provider = selected

            self._config['current_provider'] = provider
            self._save_config(self._config)
            typer.echo(f"已切换到模型提供商：{provider}")

    def remove_provider(self, provider_name: str | None = None, all_flag: bool = False):
        """移除指定或全部模型配置"""
        from questionary import confirm
        self._config = self._load_config()

        if not self._config.get('providers'):
            raise typer.Abort("当前没有可用的模型配置")

        # 处理全部删除
        if all_flag:
            confirmed = confirm("确定要删除所有模型配置吗？此操作不可恢复！").ask()
            if not confirmed:
                typer.echo("已取消删除操作")
                return   
            self._config['providers'] = {}
            self._config.pop('current_provider', None)
            self._save_config(self._config)
            typer.echo("已移除所有模型配置")
            return

        # 处理单个删除
        if not provider_name:
            raise typer.Abort("请指定要删除的提供商名称")

        if provider_name not in self._config['providers']:
            raise typer.Abort(f"提供商 {provider_name} 不存在")

        # 删除当前使用模型时的处理
        if provider_name == self._config.get('current_provider'):
            typer.echo("正在删除当前使用的模型，需要先切换模型")
            self.select_model()
            self._config = self._load_config()

        confirmed = confirm(f"确定要删除 {provider_name} 的配置吗？").ask()
        if not confirmed:
            typer.echo("已取消删除操作")
            return

        del self._config['providers'][provider_name]
        # 如果删除的是当前模型且没有切换，清空current_provider
        if provider_name == self._config.get('current_provider'):
            self._config['current_provider'] = None
        self._save_config(self._config)
        typer.echo(f"已成功移除 {provider_name} 的配置")

    def reset(self):
        """重置配置"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            self._config = {}
        except Exception as e:
            typer.echo(f"重置配置失败: {str(e)}")