
import typer
from ..config import ConfigManager
from rich.console import Console


app = typer.Typer()
console = Console()

config_help = """
    配置管理命令集\n
    
    使用示例：\n
    git-ai config \n
    git-ai config set api_key sk-123 -p openai \n
    git-ai config get max_tokens \n
    git-ai config list \n
    git-ai config reset \n
    git-ai config newpro \n
    git-ai config remove -p openai \n
    git-ai config select -p anthropic \n
    """
@app.command(help=config_help)
def config():
    pass

config_app = typer.Typer()
app.add_typer(
    config_app,
    name="config",
    short_help="配置管理系统，包含设置/查询/重置/添加/移除/选择配置项功能",
    help=config_help
    )

@config_app.command("set", help="设置指定配置项的值")
def config_set(key: str, value: str, provider_name: str = typer.Option(None, "--provider", "-p", help="服务商名称(如: openai/anthropic)")):
    """
    设置配置参数
    
    示例：
    git-ai config set api_key sk-123 -p openai
    git-ai config set max_tokens 2000 -p anthropic
    """
    config_manager = ConfigManager()
    config_manager.set(key, value, provider_name)
    typer.echo(f"成功设置 {key}={value}")


@config_app.command("get", help="查询指定配置项的当前值")
def config_get(key: str, provider_name: str = typer.Option(None, "--provider", "-p", help="服务商名称(如: openai/anthropic)")):
    """
    获取配置参数
    
    示例：
    git-ai config get api_key
    git-ai config get max_tokens -p anthropic
    """
    config_manager = ConfigManager()
    value = config_manager.get(key, provider_name)
    typer.echo(f"{key}: {value}")


@config_app.command("list", help="显示所有已存储的配置项")
def config_list():
    config_manager = ConfigManager()
    configs = config_manager.list()
    
    import json
    formatted_json = json.dumps(configs, indent=2, ensure_ascii=False)
    with Console().pager():
        Console().print(formatted_json)

@config_app.command("reset", help="清除所有配置项（不可恢复操作）")
def config_reset():
    """
    重置配置
    
    示例：
    git-ai config reset
    """
    config_manager = ConfigManager()
    config_manager.reset()
    typer.echo("配置已重置")

@config_app.command("newpro", help="交互式添加新的AI服务商配置")
def config_newpro():
    """
    添加服务商
    
    示例：
    git-ai config newpro
    """
    config_manager = ConfigManager()
    config_manager.newpro()
            

@config_app.command("remove", help="移除指定或全部模型配置")
def config_remove(
    provider_name: str = typer.Option(None, "--provider", "-p", help="指定要移除的服务商名称"),
    all_flag: bool = typer.Option(False, "--all", "-a", help="移除所有模型配置")
):
    """
    移除模型配置
    
    示例：
    git-ai config remove -p openai
    git-ai config remove --all
    """
    config_manager = ConfigManager()
    config_manager.remove_provider(provider_name, all_flag)
            

@config_app.command()
def select(
    provider_name: str = typer.Option(None, '--provider', '-p', help='服务商名称(如: openai/anthropic)')
):
    """选择当前使用的AI模型"""
    config_manager = ConfigManager()
    config_manager.select_model(provider_name)


@app.command(help="智能提交，自动生成符合规范的Git提交信息")
def push():
    """
    自动化提交命令
    
    示例：
    git-ai push
    git-ai push --review
    git-ai push --model=gpt-4
    """
    pass

@app.command(help="智能生成并提交Git commit信息")
def commit(
    preview: bool = typer.Option(False, "--preview", "-t", help="预览生成的commit信息而不直接提交"),
    retry: bool = typer.Option(False, "--retry", "-r", help="重新生成commit信息")
):
    """
    自动化生成Git提交信息
    
    示例：
    git-ai commit
    git-ai commit -t
    git-ai commit -r
    """
    from ..core import CommitGenerator
    from rich.spinner import Spinner

    config = ConfigManager()
    if not config.get("current_provider"):
        typer.echo("请先配置AI模型后再使用此功能")
        raise typer.Exit(code=1)

    generator = CommitGenerator(config)
    
    from rich.live import Live
    spinner = Spinner(name="dots", text="正在分析代码变更...")
    
    with Live(spinner, refresh_per_second=12) as live:
        diff_content = generator.get_staged_diff()
        if not diff_content:
            typer.echo("没有检测到暂存区文件变更")
            raise typer.Exit(code=1)

        live.update(Spinner(name="dots", text="正在生成commit信息..."))
        commit_msg = generator.generate_commit_message(diff_content)
    # console.print(f"[bold green]生成结果：[/bold green]\n{commit_msg}")

    if preview or retry:
        Console().print(f"[bold green]生成结果：[/bold green]\n{commit_msg}")
        return

    if typer.confirm("是否提交该信息？"):
        generator.execute_commit(commit_msg)
        typer.echo("提交成功！")
    else:
        edited_msg = typer.edit(commit_msg)
        if edited_msg:
            generator.execute_commit(edited_msg)
            typer.echo("提交成功！")

if __name__ == "__main__":
    app()