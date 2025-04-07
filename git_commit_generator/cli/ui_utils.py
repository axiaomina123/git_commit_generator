from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from typing import Dict, List

class UIUtils:
    """UI工具类，用于处理界面展示相关的功能"""
    
    console = Console()
    
    @classmethod
    def get_help_content(cls, command_name: str) -> str:
        """获取命令的帮助信息
        
        Args:
            command_name: 命令名称
            
        Returns:
            格式化后的帮助信息
        """
        help_contents = {
            "main": """   一个基于AI的Git提交信息生成工具，帮助开发者快速生成规范的提交信息。

  [bold]可用命令:[/]
  [bold]commit[/]    - 智能生成并提交Git commit信息
  [bold]quick-push[/] - 快速完成add、commit和push操作
  [bold]config[/]    - 配置管理系统

使用 [bold]git-ai COMMAND --help[/] 查看命令详细用法""",
            
            "config": """[bold]可用命令:[/]
  [bold]set[/]     - 设置指定配置项的值
  [bold]get[/]     - 查询指定配置项的当前值
  [bold]list[/]    - 显示所有已存储的配置项
  [bold]reset[/]   - 清除所有配置项
  [bold]newpro[/]  - 交互式添加新的AI服务商配置
  [bold]remove[/]  - 移除指定或全部模型配置
  [bold]select[/]  - 选择当前使用的AI模型

使用 [bold]git-ai config COMMAND --help[/] 查看命令详细用法""",
            
            "config_set": """[bold]命令:[/] git-ai config set <key> <value> [options]

[bold]参数:[/]
  <key>                  配置项名称
  <value>                配置项值
  -p, --provider TEXT   服务商名称(如: openai/anthropic)
  -h, --help            显示帮助信息

[bold]示例:[/]
  git-ai config set api_key sk-123 -p openai
  git-ai config set max_tokens 2000 -p anthropic""",
            
            "config_get": """[bold]命令:[/] git-ai config get <key> [options]

[bold]参数:[/]
  <key>                 配置项名称
  -p, --provider        服务商名称(显示当前使用的服务商信息) 
  -f, --show-full-key   显示完整的API密钥（仅当key为api_key时有效）
  -h, --help            显示帮助信息

[bold]示例:[/]
  git-ai config get current_provider
  git-ai config get max_tokens -p anthropic""",
            
            "config_list": """[bold]命令:[/] git-ai config list

[bold]参数:[/]
  -f, --show-full-key   显示完整的API密钥（默认为掩码显示）
  -h, --help            显示帮助信息

[bold]描述:[/]
  显示所有已存储的配置项，包括全局配置和各服务商配置""",
            
            "config_reset": """[bold]命令:[/] git-ai config reset

[bold]参数:[/]
  -h, --help            显示帮助信息

[bold]描述:[/]
  清除所有配置项，包括全局配置和各服务商配置（不可恢复操作）""",
            
            "config_newpro": """[bold]命令:[/] git-ai config newpro

[bold]参数:[/]
  -h, --help            显示帮助信息

[bold]描述:[/]
  交互式添加新的AI服务商配置，包括服务商名称、API密钥等信息""",
            
            "config_remove": """[bold]命令:[/] git-ai config remove [options]

[bold]参数:[/]
  -p, --provider TEXT   指定要移除的服务商名称
  -a, --all             移除所有模型配置
  -h, --help            显示帮助信息

[bold]示例:[/]
  git-ai config remove -p openai
  git-ai config remove --all""",
            
            "select": """[bold]命令:[/] git-ai config select [options]

[bold]参数:[/]
  -h, --help            显示帮助信息

[bold]描述:[/]
  选择当前使用的AI模型，设置为默认服务商""",
            
            "quick_push": """[bold]命令:[/] git-ai quick-push [options]

[bold]参数:[/]
  -r, --remote TEXT     远程仓库名称，默认为origin
  -b, --branch TEXT     分支名称，默认为当前分支
  -h, --help            显示帮助信息

[bold]描述:[/]
  快速提交命令，检测git状态并智能处理：
  - 检查是否存在冲突，如有则显示冲突文件和代码块
  - 检查暂存区文件状态，提供继续add、执行commit或退出选项
  - 交互式选择需要add的文件
  - 显示未推送的commit列表，执行push操作

[bold]示例:[/]
  git-ai quick-push
  git-ai quick-push -r upstream -b develop""",
            
            "commit": """[bold]命令:[/] git-ai commit [options]

[bold]参数:[/]
  -t, --preview         预览生成的commit信息而不直接提交
  -h, --help            显示帮助信息

[bold]描述:[/]
  智能生成并提交Git commit信息，支持预览、编辑和重新生成

[bold]示例:[/]
  git-ai commit
  git-ai commit --preview"""
        }
        
        return help_contents.get(command_name, "")

    @classmethod
    def show_multi_select(cls, prompt: str, choices: list) -> list:
        """显示多选组件"""
        from questionary import checkbox
        selected = checkbox(
            prompt,
            choices=[
                {
                    "name": f"{commit['commit_id'][:6]} {commit['author']} {commit['message']} ({commit['date']})",
                    "value": commit['commit_id']
                } for commit in choices
            ]
        ).ask()
        return selected
    
    @classmethod
    def show_panel(cls, content: str, title: str = '', style: str = "green", padding: tuple = (1, 2)):
        """显示面板
        
        Args:
            content: 面板内容
            title: 面板标题
            style: 边框样式
            padding: 内边距
        """
        panel = Panel(
            content,
            title=f'[bold {style}]Git-AI[/] {title}' if not title.startswith('[bold') else title,
            border_style=style,
            padding=padding
        )
        cls.console.print(panel)
    
    @classmethod
    def show_conflicts(cls, conflict_files: List[str], conflict_blocks: Dict[str, List[str]]):
        """显示冲突信息
        
        Args:
            conflict_files: 冲突文件列表
            conflict_blocks: 冲突代码块
        """
        cls.console.print("[bold red]错误：[/] 检测到Git冲突，请先解决以下冲突后再执行操作")
        cls.console.print("\n[bold]冲突文件列表：[/]")
        for i, file in enumerate(conflict_files, 1):
            cls.console.print(f"  {i}. {file}")
        
        if conflict_blocks:
            cls.console.print("\n[bold]冲突代码块：[/]")
            for file, blocks in conflict_blocks.items():
                cls.console.print(f"\n[bold]文件：[/] {file}")
                for i, block in enumerate(blocks, 1):
                    cls.show_panel(
                        block,
                        f"冲突 #{i}",
                        "red",
                        (1, 2)
                    )
        
        cls.console.print("\n[bold yellow]提示：[/] 请解决冲突后再执行此命令")
    
    @classmethod
    def show_staged_files(cls, files: List[str]):
        """显示已暂存文件列表
        
        Args:
            files: 已暂存文件列表
        """
        content = "\n".join([
            f"  {i}. {file}"
            for i, file in enumerate(files, 1)
        ])
        cls.show_panel(
            content,
            f"已暂存的文件 ({len(files)}个)",
            "yellow",
            (1, 2)
        )
    
    @classmethod
    def show_commit_preview(cls, commit_msg: str):
        """显示提交信息预览
        
        Args:
            commit_msg: 提交信息
        """
        cls.show_panel(
            commit_msg,
            "[bold green]提交信息预览[/]",
            "green",
            (1, 2)
        )
    
    @classmethod
    def show_spinner(cls, text: str = "正在生成commit信息..."):
        """显示加载动画
        
        Args:
            text: 加载提示文本
            
        Returns:
            Live: 加载动画上下文管理器
        """
        return Live(Spinner(name="dots", text=text))
    
    @classmethod
    def show_success(cls, message: str):
        """显示成功信息
        
        Args:
            message: 成功信息
        """
        cls.console.print(f"[bold green]{message}[/]")
    
    @classmethod
    def show_warning(cls, message: str):
        """显示警告信息
        
        Args:
            message: 警告信息
        """
        cls.console.print(f"[bold yellow]{message}[/]")
    
    @classmethod
    def show_unpushed_commits(cls, commits: List[dict]):
        """显示未推送的commit列表
        
        Args:
            commits: 未推送的commit字典列表
        """
        content = "\n".join([
            f"• [bold cyan]{commit['commit_id'][:6]}[/] {commit['author']}: "
            f"{commit['message']} ({commit['date']})"
            for commit in commits
        ])
        cls.show_panel(
            content,
            f"[bold yellow]未推送的提交 ({len(commits)}个)[/]",
            "yellow",
            (1, 2)
        )

    @classmethod
    def show_error(cls, message: str):
        """显示错误信息
        
        Args:
            message: 错误信息
        """
        cls.console.print(f"[bold red]错误：[/] {message}")