from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from typing import Dict, List

class UIUtils:
    """UI工具类，用于处理界面展示相关的功能"""
    
    console = Console()

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
    def show_panel(cls, content: str, title: str, style: str = "green", padding: tuple = (1, 2)):
        """显示面板
        
        Args:
            content: 面板内容
            title: 面板标题
            style: 边框样式
            padding: 内边距
        """
        panel = Panel(
            content,
            title=title,
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
        cls.console.print("[bold]已暂存的文件：[/]")
        for i, file in enumerate(files, 1):
            cls.console.print(f"  {i}. {file}")
    
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