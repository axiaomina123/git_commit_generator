import subprocess
import re
import logging
import os
from functools import wraps
from typing import Optional, List, Tuple, Dict, Any, Union, Callable

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def git_command_handler(func: Callable) -> Callable:
    """装饰器：统一处理Git命令执行异常"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            error_msg = f"Git命令执行失败: {str(e)}"
            if hasattr(e, 'stderr') and e.stderr:
                error_msg += f"\n错误详情: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"{func.__name__}执行失败: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    return wrapper

class GitOperations:
    """封装所有Git相关的操作"""
    
    @staticmethod
    def run_git_command(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """执行Git命令的通用方法
        
        Args:
            cmd: Git命令及其参数列表
            check: 是否检查命令执行状态
            
        Returns:
            subprocess.CompletedProcess: 命令执行结果
        """
        # 添加编码处理，确保中文路径正确识别
        return subprocess.run(cmd, check=check, encoding='utf-8', errors='ignore', capture_output=True)
    
    @classmethod
    def get_staged_diff(cls):
        """获取暂存区的差异"""
        result = cls.run_git_command(['git', 'diff', '--cached'])
        return result.stdout.strip()
    
    @classmethod
    def get_unstaged_files(cls) -> List[str]:
        """获取未暂存的文件列表"""
        # 获取未跟踪的文件
        untracked = cls.run_git_command(
            ['git', 'ls-files', '--others', '--exclude-standard']
        ).stdout.strip().splitlines()
        
        # 获取已修改但未暂存的文件
        modified = cls.run_git_command(
            ['git', 'diff', '--name-only']
        ).stdout.strip().splitlines()
        
        # 合并两个列表并去重
        files = list(set(untracked + modified))
        return files
    
    @classmethod
    def get_staged_files(cls):
        """获取已暂存但未提交的文件列表"""
        result = cls.run_git_command(
            ['git', 'diff', '--name-only', '--cached']
        ).stdout.strip().splitlines()
        return result or []
    
    @classmethod
    def execute_add(cls, files: List[str]) -> bool:
        """添加文件到暂存区"""
        if not files:
            return False
        
        # 改进路径处理逻辑
        normalized_files = []
        for f in files:
            try:
                # 先标准化路径
                norm_path = os.path.normpath(f)
                # 确保路径存在
                if not os.path.exists(norm_path):
                    logger.warning(f"文件路径不存在: {norm_path}")
                    continue
                # 处理特殊字符
                encoded_path = norm_path.encode('utf-8').decode('utf-8')
                normalized_files.append(encoded_path)
            except Exception as e:
                logger.error(f"处理文件路径时出错: {f}, 错误: {str(e)}")
                continue
                
        if not normalized_files:
            logger.error("没有有效的文件路径可以添加")
            return False
            
        cls.run_git_command(['git', 'add'] + normalized_files)
        return True
    
    @classmethod
    def execute_commit(cls, message: str) -> bool:
        """执行提交操作"""
        cls.run_git_command(['git', 'commit', '-m', message])
        return True
    
    @classmethod
    @git_command_handler
    def execute_push(cls, remote: str = 'origin', branch: str = '', commit_ids: List[str] = []) -> bool:
        """推送到远程仓库
        
        Args:
            remote: 远程仓库名称
            branch: 目标分支名称
            commit_ids: 要推送的提交ID列表，为空则推送所有未推送的提交
        """
        if branch:
            # 检查远程分支是否存在
            check_branch_cmd = ['git', 'ls-remote', '--heads', remote, branch]
            branch_exists = cls.run_git_command(check_branch_cmd).stdout != ''
            
            if not branch_exists:
                from questionary import confirm
                if not confirm(f"远程分支 {branch} 不存在，是否创建？").ask():
                    logger.info("用户取消推送操作")
                    return False
                push_cmd = ['git', 'push', remote, f'HEAD:refs/heads/{branch}']
            else:
                push_cmd = ['git', 'push', remote, branch]
        else:
            push_cmd = ['git', 'push', remote]
        
        # 如果指定了commit_ids，使用cherry-pick方式推送
        # if commit_ids:
        #     # 使用指定的提交ID进行推送
        #     commit_range = f"{commit_ids[0]}^..{commit_ids[-1]}"
        #     push_cmd = ['git', 'push', remote, commit_range]
        #     logger.info(f"正在推送提交范围: {commit_range}")
        
        result = cls.run_git_command(push_cmd)
        if result.returncode == 0:
            logger.info("推送成功")
            return True
        return False
    
    @classmethod
    def execute_reset(cls) -> bool:
        """撤销暂存区的更改"""
        cls.run_git_command(['git', 'reset'])
        return True
    
    @classmethod
    def get_current_branch(cls):
        """获取当前分支名称"""
        try:
            result = cls.run_git_command(['git', 'branch', '--show-current'])
            return result.stdout.strip()
        except Exception as e:
            error_msg = f"获取当前分支失败: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    @classmethod
    @git_command_handler
    def get_unpushed_commits(cls) -> List[dict]:
        """获取未推送的提交列表"""
        # 获取当前分支名称
        current_branch = cls.get_current_branch()
        logger.info(f"当前分支: {current_branch}")
        
        # 检查是否设置上游分支
        try:
            cls.run_git_command(['git', 'rev-parse', '--abbrev-ref', '@{u}'], check=True)
        except Exception as e:
            error_msg = f"当前分支 {current_branch} 未关联远程分支\n解决方案: git branch --set-upstream-to=origin/{current_branch}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # 获取未推送的提交
        result = cls.run_git_command(
            ['git', 'log', f'origin/{current_branch}..HEAD', '--pretty=format:%H||%an||%ad||%s']
        )
        commit_lines = result.stdout.strip().splitlines()
        
        # 解析提交信息
        commits = []
        for line in commit_lines:
            parts = line.split('||')
            if len(parts) >= 4:
                commit = {
                    'commit_id': parts[0],
                    'author': parts[1],
                    'date': parts[2],
                    'message': parts[3]
                }
                commits.append(commit)
                logger.debug(f"找到未推送的提交: {commit['commit_id']} - {commit['message']}")
        
        return commits   
    
    @classmethod
    @git_command_handler
    def check_conflicts(cls) -> Tuple[bool, List[str], Dict[str, List[str]]]:
        """检查是否存在冲突文件
        
        Returns:
            Tuple[bool, List[str], Dict[str, List[str]]]: 
            - 是否存在冲突
            - 冲突文件列表
            - 冲突文件的冲突块内容
        """
        result = cls.run_git_command(['git', 'ls-files', '--unmerged'])
        unmerged_files = result.stdout.strip().splitlines()
        
        if not unmerged_files:
            logger.info("未发现冲突文件")
            return False, [], {}
        
        # 提取冲突文件路径并去重
        conflict_files = {parts[3] for line in unmerged_files 
                        if line.strip() and len(parts := line.strip().split()) >= 4}
        
        if not conflict_files:
            logger.info("未发现有效的冲突文件")
            return False, [], {}
        
        logger.info(f"发现{len(conflict_files)}个冲突文件")
        conflict_files = list(conflict_files)
        conflict_blocks = {}
        
        # 提取冲突代码块
        for file in conflict_files:
            try:
                if not os.path.exists(file):
                    error_msg = f"冲突文件不存在: {file}"
                    logger.error(error_msg)
                    conflict_blocks[file] = [error_msg]
                    continue
                    
                with open(file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                conflict_pattern = r'<<<<<<< .*?\n(.*?)=======\n(.*?)>>>>>>> .*?\n'
                matches = list(re.finditer(conflict_pattern, content, re.DOTALL))
                
                if not matches:
                    logger.warning(f"文件{file}未找到冲突标记")
                    continue
                
                blocks = []
                for match in matches:
                    try:
                        ours = match.group(1).strip()
                        theirs = match.group(2).strip()
                        blocks.append(f"<<<<<<< HEAD\n{ours}\n=======\n{theirs}\n>>>>>>> BRANCH")
                    except Exception as e:
                        logger.error(f"解析冲突块时出错: {str(e)}")
                        continue
                
                if blocks:
                    conflict_blocks[file] = blocks
                    logger.info(f"文件{file}发现{len(blocks)}个冲突块")
            except Exception as e:
                error_msg = f"无法读取文件{file}的冲突内容: {str(e)}"
                logger.error(error_msg)
                conflict_blocks[file] = [error_msg]
    
        return True, conflict_files, conflict_blocks