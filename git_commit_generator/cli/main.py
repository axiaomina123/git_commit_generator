import click
import typer
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from ..config import ConfigManager
from ..core import CommitGenerator
from git_commit_generator.git_operations import GitOperations
from .ui_utils import UIUtils

app = typer.Typer()
config_app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})
app.add_typer(
    config_app,
    name="config",
    short_help="配置管理系统，包含设置/查询/重置/添加/移除/选择配置项功能",
    )

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, 
help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help or ctx.invoked_subcommand is None:
        UIUtils.show_panel(UIUtils.get_help_content("main"), "智能提交工具 🚀")

@config_app.callback(invoke_without_command=True)
def config_callback(ctx: typer.Context, 
help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help or ctx.invoked_subcommand is None:
        UIUtils.show_panel(UIUtils.get_help_content("config"), "配置管理系统 🔧")

@config_app.command("get", help="查询指定配置项的当前值")
def config_get(key: str = typer.Argument(None), 
               provider_name: str = typer.Option(None, "--provider", "-p", help="服务商名称(如: openai/anthropic)"), 
               show_full_key: bool = typer.Option(False, "--show-full-key", "-f", help="显示完整的API密钥（仅当key为api_key时有效）"),
               help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help:
        UIUtils.show_panel(UIUtils.get_help_content("config_get"), "查询配置项")
        raise typer.Exit()
    
    if not key and not provider_name:
        UIUtils.show_error("参数错误，请输入完整的配置项名称")
        raise typer.Exit(code=1)
    
    config_manager = ConfigManager()
    result = config_manager.get(key, provider_name, mask_api_key=not show_full_key)
    if result[0]:
        if provider_name:
            case = f"{provider_name}/{key}: " if key else f"{provider_name}: "
        else:
            case = f"{key}: "
        UIUtils.show_success(message=f"{case}{result[1]}")
    else:
        UIUtils.show_error(message=result[1])
    

@config_app.command("list", help="显示所有已存储的配置项")
def config_list(show_full_key: bool = typer.Option(False, "--show-full-key", "-f", help="显示完整的API密钥"),
               help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help:
        UIUtils.show_panel(UIUtils.get_help_content("config_list"), "配置列表")
        raise typer.Exit()
    
    config_manager = ConfigManager()
    result = config_manager.config_list(mask_api_key=not show_full_key)
    
    if result[0]:
        import json
        formatted_json = json.dumps(result[1], indent=2, ensure_ascii=False)
        with Console().pager():
            UIUtils.show_panel(content=formatted_json, title="配置列表", padding=(0,1))
    else:
        UIUtils.show_error(message=result[1])

@config_app.command("set", help="设置指定配置项的值")
def config_set(key: str= typer.Argument(None), value: str = typer.Argument(None), provider_name: str = typer.Option(None, "--provider", "-p", help="服务商名称(如: openai/anthropic)"), 
help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help:
        UIUtils.show_panel(UIUtils.get_help_content("config_set"), "设置配置项")
        raise typer.Exit()
    if not key or not value:
        UIUtils.show_error("参数错误，请输入完整的配置项名称和值")
        raise typer.Exit(code=1)

    config_manager = ConfigManager()
    result = config_manager.config_set(key, value, provider_name)
    if result[0]:
        UIUtils.show_success(message=result[1])
    else:
        UIUtils.show_error(message=result[1])

@config_app.command("reset", help="清除所有配置项（不可恢复操作）")
def config_reset(help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help:
        UIUtils.show_panel(UIUtils.get_help_content("config_reset"), "重置配置")
        raise typer.Exit()
    
    config_manager = ConfigManager()
    result = config_manager.config_reset()
    if result[0]:
        UIUtils.show_success(message=f"配置已重置")
    else:
        UIUtils.show_error(message=result[1])
    

@config_app.command("newpro", help="交互式添加新的AI服务商配置")
def config_newpro(help: bool = typer.Option(None, "--help", "-h", is_eager=True)):
    if help:
        UIUtils.show_panel(UIUtils.get_help_content("config_newpro"), "添加服务商")
        raise typer.Exit()
    
    config_manager = ConfigManager()
    result =  config_manager.config_newpro()
    if result[0]:
        UIUtils.show_success(message=f"成功添加新的AI服务商配置")
    else:
        UIUtils.show_error(message=result[1])

@config_app.command("remove", help="移除指定或全部模型配置")
def config_remove(
    provider_name: str = typer.Option(None, "--provider", "-p", help="指定要移除的服务商名称"),
    all_flag: bool = typer.Option(False, "--all", "-a", help="移除所有模型配置"),
    help: bool = typer.Option(None, "--help", "-h", is_eager=True)
):
    if help:
        UIUtils.show_panel(UIUtils.get_help_content("config_remove"), "移除模型配置")
        raise typer.Exit()
    
    config_manager = ConfigManager()
    result = config_manager.config_remove(provider_name, all_flag)
    if result[0]:
        UIUtils.show_success(message=f"成功移除模型配置")
    else:
        UIUtils.show_error(message=result[1])

@config_app.command(help="选择当前使用的AI模型")
def select(
    help: bool = typer.Option(None, "--help", "-h", is_eager=True)
):
    """选择当前使用的AI模型"""
    if help:
        UIUtils.show_panel(UIUtils.get_help_content("select"), "选择AI模型")
        raise typer.Exit()
    
    config_manager = ConfigManager()
    result = config_manager.select_model()
    if result[0]:
        UIUtils.show_success(message=f"成功选择模型 {result[1]}")
    else:
        UIUtils.show_error(message=result[1])


@app.command(help="快速提交，一键完成add、commit和push操作")
def quick_push(
    remote: str = typer.Option("origin", "--remote", "-r", help="远程仓库名称"),
    branch: str = typer.Option("", "--branch", "-b", help="分支名称，默认为当前分支"),
    help: bool = typer.Option(None, "--help", "-h", is_eager=True)
):
    if help:
        UIUtils.show_panel(UIUtils.get_help_content("quick_push"), "快速提交")
        raise typer.Exit()
    
    try:
        generator = CommitGenerator(ConfigManager())
        git_op = GitOperations()
        branch = branch if branch else git_op.get_current_branch()
        
        # 检查是否存在冲突
        has_conflicts, conflict_files, conflict_blocks = generator.check_conflicts()
        if has_conflicts:
            UIUtils.show_conflicts(conflict_files, conflict_blocks)
            raise typer.Exit(code=1)
        
        # 检查暂存区状态
        staged_files = git_op.get_staged_files()
        if staged_files:
            UIUtils.show_staged_files(staged_files)
            from questionary import select
            choice = select(
                "检测到暂存区有未commit的文件，请选择操作：",
                choices=[
                    {"name": "1. 继续add", "value": "1"},
                    {"name": "2. 执行commit", "value": "2"},
                    {"name": "3. 退出", "value": "3"}
                ]
            ).ask()
        
            if choice == "1":
                # 处理未暂存的文件
                unstaged_files = git_op.get_unstaged_files()
                if unstaged_files:
                    from questionary import checkbox
                    selected = checkbox(
                        "请选择要add的文件：",
                        choices=unstaged_files
                    ).ask()                    
                    if selected:
                        git_op.execute_add(selected)
                        UIUtils.show_success("文件已添加到暂存区")
                    else:
                        UIUtils.show_warning("未选择任何文件，已跳过add操作")
                else:
                    UIUtils.show_warning("没有未暂存的文件，已跳过add操作")
                    
            elif choice == "2":
                pass
            else:
                UIUtils.show_warning("操作已取消")
                return
        else:
            # 处理未暂存的文件
            unstaged_files = git_op.get_unstaged_files()
            if unstaged_files:
                from questionary import checkbox
                selected = checkbox(
                    "请选择要add的文件：",
                    choices=unstaged_files
                ).ask()                
                if selected:
                    git_op.execute_add(selected)
                    UIUtils.show_success("文件已添加到暂存区")
                else:
                    UIUtils.show_warning("未选择任何文件，已跳过add操作")
            else:
                UIUtils.show_warning("没有未暂存的文件，已跳过add操作")       
        if git_op.get_staged_files():
            # 生成并执行commit
            diff_content = git_op.get_staged_diff()
            while True:
                with Live(Spinner(name="dots", text="正在生成commit信息...")):
                    commit_msg = _generate_commit(generator, diff_content)
                UIUtils.show_commit_preview(commit_msg)
                try:
                    choice = typer.prompt("请选择操作 [u]使用/q退出/e编辑/r重新生成").lower()
                except click.Abort:
                    raise KeyboardInterrupt
                
                if choice == 'u':
                    generator.execute_commit(commit_msg)
                    UIUtils.show_success("提交成功！")
                    break
                elif choice == 'q':
                    UIUtils.show_warning("已取消提交")
                    break
                elif choice == 'e':
                    edited_msg = typer.edit(commit_msg)
                    if edited_msg:
                        generator.execute_commit(edited_msg)
                        UIUtils.show_success("提交成功！")
                        break
                elif choice == 'r':
                    continue
                else:
                    UIUtils.show_error("无效的选择，请重新输入")
        # 检查未推送的提交
        unpushed_commits = git_op.get_unpushed_commits()
        if unpushed_commits:
            # 展示未推送提交
            UIUtils.show_unpushed_commits(unpushed_commits)
            
            # 自动选择全部提交
            selected_ids = [commit['commit_id'] for commit in unpushed_commits]
            
            if typer.confirm(f"确认推送以下{len(selected_ids)}个提交到{remote}/{branch}分支？", default=True):
                git_op.execute_push(remote, branch, selected_ids)
                UIUtils.show_success(f"成功推送 {len(selected_ids)} 个提交！")
                
        else:
            UIUtils.show_warning("当前分支没有需要推送的提交")
    
    except KeyboardInterrupt:
        UIUtils.show_warning("操作已取消")
        return
    except Exception as e:
        UIUtils.show_error(str(e))
        raise typer.Exit(code=1)
    

def _generate_commit(generator, diff_content):
    """生成commit信息核心逻辑"""
    try:
        return generator.generate_commit_message(diff_content)
    except Exception as e:
        UIUtils.show_error(f"生成失败: {str(e)}")
        raise typer.Exit(code=1)


def _preview_commit_msg(commit_msg):
    """处理预览模式逻辑"""
    UIUtils.show_panel(content=commit_msg, title="commit信息预览", padding=(1, 2))




@app.command(help="智能生成并提交Git commit信息")
def commit(
    preview: bool = typer.Option(False, "--preview", "-t", help="预览生成的commit信息而不直接提交"),
    help: bool = typer.Option(None, "--help", "-h", is_eager=True)
):
    if help:
        UIUtils.show_panel(UIUtils.get_help_content("commit"), "快速提交")
        raise typer.Exit()
    
    config = ConfigManager()
    if not config.get("current_provider"):
        UIUtils.show_error("请先配置AI模型后再使用此功能")
        raise typer.Exit(code=1)

    try:
        generator = CommitGenerator(config)
        
        # 检查是否存在冲突
        has_conflicts, conflict_files, conflict_blocks = generator.check_conflicts()
        if has_conflicts:
            UIUtils.show_error("检测到Git冲突，请先解决以下冲突后再执行操作")
            Console().print("\n[bold]冲突文件列表：[/]")
            for i, file in enumerate(conflict_files, 1):
                Console().print(f"  {i}. {file}")
            
            # 显示冲突代码块
            if conflict_blocks:
                Console().print("\n[bold]冲突代码块：[/]")
                for file, blocks in conflict_blocks.items():
                    Console().print(f"\n[bold]文件：[/] {file}")
                    for i, block in enumerate(blocks, 1):
                        UIUtils.show_panel(content=block, title=f"冲突 #{i}", style="yellow", padding=(1, 2))
            
            UIUtils.show_error("请解决冲突后再执行操作")
            raise typer.Exit(code=1)
            
        diff_content = generator.get_staged_diff()
        
        if not diff_content:
            UIUtils.show_warning("没有检测到暂存区文件变更")
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
                UIUtils.show_success("提交成功！")
                break
            elif choice == 'q':
                UIUtils.show_warning("已取消提交")
                break
            elif choice == 'e':
                edited_msg = typer.edit(commit_msg)
                if edited_msg:
                    generator.execute_commit(edited_msg)
                    UIUtils.show_success("提交成功！")
                    break
            elif choice == 'r':
                continue
            else:
                UIUtils.show_error("无效选项，请重新选择")

    except KeyboardInterrupt:
        UIUtils.show_warning("操作已取消")
        return
    except Exception as e:
        UIUtils.show_error(str(e))
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()