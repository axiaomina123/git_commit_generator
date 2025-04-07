import subprocess
import re
from typing import Optional, List, Tuple, Dict

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
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=check
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git命令执行失败: {str(e)}")
    
    @classmethod
    def get_staged_diff(cls) -> str:
        """获取暂存区的差异"""
        result = cls.run_git_command(['git', 'diff', '--cached'])
        return result.stdout.strip() if result.stdout else ''
    
    @classmethod
    def get_unstaged_files(cls) -> List[str]:
        """获取未暂存的文件列表"""
        # 获取未跟踪的文件
        untracked = cls.run_git_command(
            ['git', 'ls-files', '--others', '--exclude-standard']
        )
        
        # 获取已修改但未暂存的文件
        modified = cls.run_git_command(
            ['git', 'diff', '--name-only']
        )
        
        files = []
        if untracked.stdout:
            files.extend(untracked.stdout.strip().split('\n'))
        if modified.stdout:
            files.extend(modified.stdout.strip().split('\n'))
            
        return [f for f in files if f.strip()]
    
    @classmethod
    def get_staged_files(cls) -> List[str]:
        """获取已暂存但未提交的文件列表"""
        result = cls.run_git_command(['git', 'diff', '--name-only', '--cached'])
        if result.stdout.strip():
            return [f for f in result.stdout.strip().split('\n') if f.strip()]
        return []
    
    @classmethod
    def execute_add(cls, files: List[str]) -> bool:
        """添加文件到暂存区"""
        if not files:
            return False
        cls.run_git_command(['git', 'add'] + files)
        return True
    
    @classmethod
    def execute_commit(cls, message: str) -> bool:
        """执行提交操作"""
        cls.run_git_command(['git', 'commit', '-m', message])
        return True
    
    @classmethod
    def execute_push(cls, remote: str = 'origin', branch: str = '', commit_ids: List[str] = []) -> bool:
        """推送到远程仓库"""
        try:
            if branch:
                # 检查远程分支是否存在
                check_branch_cmd = ['git', 'ls-remote', '--heads', remote, branch]
                branch_exists = cls.run_git_command(check_branch_cmd).stdout.strip() != ''

                if not branch_exists:
                    from questionary import confirm
                    if not confirm(f"远程分支 {branch} 不存在，是否创建？").ask():
                        raise RuntimeError("用户取消推送操作")
                    result = cls.run_git_command(['git', 'push', remote, f'HEAD:refs/heads/{branch}'])
                else:
                    result = cls.run_git_command(['git', 'push', remote, branch])
            else:
                result = cls.run_git_command(['git', 'push', remote])
            
            # 执行推送并捕获详细错误
            if result.returncode != 0:
                raise RuntimeError(f"推送失败: {result.returncode}\n{result.stderr}")
            return True
        except Exception as e:
            raise RuntimeError(f"推送操作失败: {str(e)}")
    
    @classmethod
    def execute_reset(cls) -> bool:
        """撤销暂存区的更改"""
        cls.run_git_command(['git', 'reset'])
        return True
    
    @classmethod
    def has_staged_changes(cls) -> bool:
        """检查是否有已暂存但未提交的更改"""
        try:
            result = cls.run_git_command(
                ['git', 'diff', '--cached', '--quiet'],
                check=False
            )
            return result.returncode == 1
        except Exception:
            return False
    
    @classmethod
    def get_unpushed_commits(cls) -> List[dict]:
        """获取未推送的提交列表"""
        try:
    
            # 获取当前分支名称
            branch_result = cls.run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
            current_branch = branch_result.stdout.strip()
            
            # 检查是否设置上游分支
            try:
                cls.run_git_command(['git', 'rev-parse', '--abbrev-ref', '@{u}'], check=True)
            except subprocess.CalledProcessError:
                raise RuntimeError(f"当前分支 {current_branch} 未关联远程分支\n请执行: git branch --set-upstream-to=origin/{current_branch}")
            
            # 获取未推送的提交
            result = cls.run_git_command(
                ['git', 'log', f'origin/{current_branch}..HEAD', '--pretty=format:%H||%an||%ad||%s']
            )
        except subprocess.CalledProcessError as e:
            error_msg = f"Git命令执行失败: {e}\n可能原因：\n1. 远程仓库未配置\n2. 分支未关联远程\n3. 网络连接问题\n4. 权限不足\n解决方案：\n• 执行 git remote -v 检查远程仓库\n• 执行 git branch --set-upstream-to=origin/<分支名> 关联分支"
            raise Exception(error_msg) from e
        
        commits = []
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                parts = line.split('||')
                if len(parts) >= 4:
                    commits.append({
                        'commit_id': parts[0],
                        'author': parts[1],
                        'date': parts[2],
                        'message': parts[3]
                    })
        return commits   
    
    @classmethod
    def check_conflicts(cls) -> Tuple[bool, List[str], Dict[str, List[str]]]:
        """检查是否存在冲突文件"""
        result = cls.run_git_command(['git', 'ls-files', '--unmerged'])
        
        if not result.stdout.strip():
            return False, [], {}
        
        conflict_files = set()
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 4:
                    conflict_files.add(parts[3])
        
        conflict_files = list(conflict_files)
        conflict_blocks = {}
        
        for file in conflict_files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                conflict_pattern = r'<<<<<<< .*?\n(.*?)=======\n(.*?)>>>>>>> .*?\n'
                matches = re.finditer(conflict_pattern, content, re.DOTALL)
                
                blocks = []
                for match in matches:
                    ours = match.group(1).strip()
                    theirs = match.group(2).strip()
                    blocks.append(f"<<<<<<< HEAD\n{ours}\n=======\n{theirs}\n>>>>>>> BRANCH")
                
                if blocks:
                    conflict_blocks[file] = blocks
            except Exception as e:
                conflict_blocks[file] = [f"无法读取冲突内容: {str(e)}"]
        
        return True, conflict_files, conflict_blocks