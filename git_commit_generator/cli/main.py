import click
import typer
from ..config import ConfigManager
from ..core import CommitGenerator
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.panel import Panel


app = typer.Typer()
console = Console()
config_app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})
app.add_typer(
    config_app,
    name="config",
    short_help="配置管理系统，包含设置/查询/重置/添加/移除/选择配置项功能",
    )

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, 
help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    panel = Panel(     
  """   一个基于AI的Git提交信息生成工具，帮助开发者快速生成规范的提交信息。

  [bold]可用命令:[/]
  [bold]commit[/]  - 智能生成并提交Git commit信息
  [bold]config[/]  - 配置管理系统

使用 [bold]git-ai COMMAND --help[/] 查看命令详细用法""",
        title="[bold green]Git-AI[/] 智能提交工具 🚀",
        border_style="green",
        padding=(1, 2)
    )
    if help:
        console.print(panel)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(panel)

@config_app.callback(invoke_without_command=True)
def config_callback(ctx: typer.Context, 
help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    panel = Panel(
        """[bold]可用命令:[/]
  [bold]set[/]     - 设置指定配置项的值
  [bold]get[/]     - 查询指定配置项的当前值
  [bold]list[/]    - 显示所有已存储的配置项
  [bold]reset[/]   - 清除所有配置项
  [bold]newpro[/]  - 交互式添加新的AI服务商配置
  [bold]remove[/]  - 移除指定或全部模型配置
  [bold]select[/]  - 选择当前使用的AI模型

使用 [bold]git-ai config COMMAND --help[/] 查看命令详细用法""",
        title="[bold green]Git-AI[/] 配置管理系统 🔧",
        border_style="green",
        padding=(1, 2)
    )
    if help:
        console.print(panel)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(panel)


@config_app.command("set", help="设置指定配置项的值")
def config_set(key: str= typer.Argument(None), value: str = typer.Argument(None), provider_name: str = typer.Option(None, "--provider", "-p", help="服务商名称(如: openai/anthropic)"), 
help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help:
        panel = Panel(
            """[bold]命令:[/] git-ai config set <key> <value> [options]

[bold]参数:[/]
  <key>                  配置项名称
  <value>                配置项值
  -p, --provider TEXT   服务商名称(如: openai/anthropic)
  -h, --help            显示帮助信息

[bold]示例:[/]
  git-ai config set api_key sk-123 -p openai
  git-ai config set max_tokens 2000 -p anthropic""",
            title="[bold green]Git-AI[/] 设置配置项",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)
        raise typer.Exit()
    
    # 检查必需参数
    if key is None or value is None:
        console.print("[bold red]错误:[/] 缺少必需参数。使用 --help 查看帮助信息。")
        raise typer.Exit(code=1)
    
    config_manager = ConfigManager()
    config_manager.set(key, value, provider_name)
    panel = Panel(
        f"[bold green]成功设置[/] {key}={value}",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)

@config_app.command("get", help="查询指定配置项的当前值")
def config_get(key: str = typer.Argument(None), provider_name: str = typer.Option(None, "--provider", "-p", 
help="服务商名称(如: openai/anthropic)"), 
help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help:
        panel = Panel(
            """[bold]命令:[/] git-ai config get <key> [options]

[bold]参数:[/]
  <key>                  配置项名称
  -p, --provider TEXT   服务商名称(如: openai/anthropic)
  -h, --help            显示帮助信息

[bold]示例:[/]
  git-ai config get api_key
  git-ai config get max_tokens -p anthropic""",
            title="[bold green]Git-AI[/] 查询配置项",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)
        raise typer.Exit()
    
    config_manager = ConfigManager()
    value = config_manager.get(key, provider_name)
    panel = Panel(
        f"{key}: {value}",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)

@config_app.command("list", help="显示所有已存储的配置项")
def config_list(help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help:
        panel = Panel(
            """[bold]命令:[/] git-ai config list

[bold]参数:[/]
  -h, --help            显示帮助信息

[bold]描述:[/]
  显示所有已存储的配置项，包括全局配置和各服务商配置""",
            title="[bold green]Git-AI[/] 配置列表",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)
        raise typer.Exit()
    
    config_manager = ConfigManager()
    configs = config_manager.list()
    
    import json
    formatted_json = json.dumps(configs, indent=2, ensure_ascii=False)
    panel = Panel(
        formatted_json,
        title="[bold green]配置列表[/]",
        border_style="green",
        padding=(1, 2)
    )
    with Console().pager():
        Console().print(panel)

@config_app.command("reset", help="清除所有配置项（不可恢复操作）")
def config_reset(help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help:
        panel = Panel(
            """[bold]命令:[/] git-ai config reset

[bold]参数:[/]
  -h, --help            显示帮助信息

[bold]描述:[/]
  清除所有配置项，包括全局配置和各服务商配置（不可恢复操作）""",
            title="[bold green]Git-AI[/] 重置配置",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)
        raise typer.Exit()
    
    config_manager = ConfigManager()
    config_manager.reset()
    panel = Panel(
        "[bold yellow]配置已重置[/]",
        border_style="yellow",
        padding=(1, 2)
    )
    console.print(panel)

@config_app.command("newpro", help="交互式添加新的AI服务商配置")
def config_newpro(help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help:
        panel = Panel(
            """[bold]命令:[/] git-ai config newpro

[bold]参数:[/]
  -h, --help            显示帮助信息

[bold]描述:[/]
  交互式添加新的AI服务商配置，包括服务商名称、API密钥等信息""",
            title="[bold green]Git-AI[/] 添加服务商",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)
        raise typer.Exit()
    
    config_manager = ConfigManager()
    config_manager.newpro()
    panel = Panel(
        "[bold green]成功添加新的AI服务商配置[/]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)

@config_app.command("remove", help="移除指定或全部模型配置")
def config_remove(
    provider_name: str = typer.Option(None, "--provider", "-p", help="指定要移除的服务商名称"),
    all_flag: bool = typer.Option(False, "--all", "-a", help="移除所有模型配置"),
    help: bool = typer.Option(None, "--help", "-h", is_eager=True)
):
    if help:
        panel = Panel(
            """[bold]命令:[/] git-ai config remove [options]

[bold]参数:[/]
  -p, --provider TEXT   指定要移除的服务商名称
  -a, --all             移除所有模型配置
  -h, --help            显示帮助信息

[bold]示例:[/]
  git-ai config remove -p openai
  git-ai config remove --all""",
            title="[bold green]Git-AI[/] 移除模型配置",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)
        raise typer.Exit()
    
    config_manager = ConfigManager()
    config_manager.remove_provider(provider_name, all_flag)
    panel = Panel(
        "[bold yellow]成功移除指定的模型配置[/]",
        border_style="yellow",
        padding=(1, 2)
    )
    console.print(panel)

@config_app.command(help="选择当前使用的AI模型")
def select(
    help: bool = typer.Option(None, "--help", "-h", is_eager=True)
):
    """选择当前使用的AI模型"""
    if help:
        panel = Panel(
            """[bold]命令:[/] git-ai config select [options]

[bold]参数:[/]
  -h, --help            显示帮助信息

[bold]描述:[/]
  选择当前使用的AI模型，设置为默认服务商""",
            title="[bold green]Git-AI[/] 选择AI模型",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)
        raise typer.Exit()
    
    config_manager = ConfigManager()
    provider = config_manager.select_model()
    if provider is None:
        raise typer.Exit(code=1)
    panel = Panel(
        f"[bold green]成功选择[/] {provider}",
        border_style="green",
        padding=(0, 1) 
    )
    console.print(panel)


@app.command(help="智能提交，自动生成符合规范的Git提交信息")
def push(help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help:
        panel = Panel(
            """[bold]命令:[/] git-ai push [options]

[bold]参数:[/]
  -h, --help            显示帮助信息

[bold]描述:[/]
  自动化提交命令，生成符合规范的Git提交信息并执行提交

[bold]示例:[/]
  git-ai push""",
            title="[bold green]Git-AI[/] 智能提交",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)
        raise typer.Exit()
    
    pass

def _generate_commit(generator, diff_content):
    """生成commit信息核心逻辑"""
    try:
        return generator.generate_commit_message(diff_content)
    except Exception as e:
        console.print(f"[bold red]生成失败:[/] {str(e)}")
        raise typer.Exit(code=1)


def _preview_commit_msg(commit_msg):
    """处理预览模式逻辑"""
    panel = Panel(
        commit_msg,
        title="Commit Preview",
        border_style="green",
        padding=(1, 4)
    )
    console.print(panel)




@app.command(help="智能生成并提交Git commit信息")
def commit(
    preview: bool = typer.Option(False, "--preview", "-t", help="预览生成的commit信息而不直接提交"),
    help: bool = typer.Option(None, "--help", "-h", is_eager=True)
):
    if help:
        panel = Panel(
            """[bold]命令:[/] git-ai commit [options]

[bold]参数:[/]
  -t, --preview         预览生成的commit信息而不直接提交
  -h, --help            显示帮助信息

[bold]描述:[/]
  智能生成并提交Git commit信息，支持预览、编辑和重新生成

[bold]示例:[/]
  git-ai commit
  git-ai commit --preview""",
            title="[bold green]Git-AI[/] 智能提交",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)
        raise typer.Exit()
    
    config = ConfigManager()
    if not config.get("current_provider"):
        console.print("[bold red]错误：[/] 请先配置AI模型后再使用此功能")
        raise typer.Exit(code=1)

    try:
        generator = CommitGenerator(config)
        diff_content = generator.get_staged_diff()
        
        if not diff_content:
            console.print("[bold yellow]警告：[/] 没有检测到暂存区文件变更")
            raise typer.Exit(code=1)

        while True:
            with Live(Spinner(name="dots", text="正在生成commit信息...")):
                commit_msg = _generate_commit(generator, diff_content)
            _preview_commit_msg(commit_msg)
            if preview:
                return  # 确保预览模式直接退出
            try:
                choice = typer.prompt("请选择操作 [u]使用/q退出/e编辑/r重新生成").lower()
            except click.Abort:
                raise KeyboardInterrupt
            
            if choice == 'u':
                generator.execute_commit(commit_msg)
                console.print("[bold green]提交成功！[/]")
                break
            elif choice == 'q':
                console.print("[yellow]已取消提交[/]")
                break
            elif choice == 'e':
                edited_msg = typer.edit(commit_msg)
                if edited_msg:
                    generator.execute_commit(edited_msg)
                    console.print("[bold green]提交成功！[/]")
                    break
            elif choice == 'r':
                continue
            else:
                console.print("[red]无效选项，请重新选择[/]")

    # except typer.Exit:
        # raise
    except KeyboardInterrupt:
        console.print("[yellow]\n操作已取消[/]")
        return
    except Exception as e:
        console.print(f"[bold red]发生错误：[/] {str(e)}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()