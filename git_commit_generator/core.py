from git_commit_generator.config import ConfigManager
import subprocess
import re
from typing import Optional, List, Tuple, Dict
from git_commit_generator.models.adapter import ModelAdapter

class CommitGenerator:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.current_provider = config.get('current_provider')

    def get_staged_diff(self) -> Optional[str]:
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=True
            )
            return result.stdout.strip() if result.stdout else ''
        except subprocess.CalledProcessError as e:
            return ''

    def generate_commit_message(self, diff_content: str) -> str:
        prompt = self._build_prompt(diff_content)
        try:
            return ModelAdapter(self.current_provider).generate(prompt)
        except Exception as e:
            raise RuntimeError(f"API调用失败: {str(e)}")

    def _build_prompt(self, diff_content: str) -> str:
        return f"""
        根据以下代码变更生成规范的Git提交信息：
        
        【代码变更】
        {diff_content}
        
        【生成要求】
        1. 识别修改类型（功能新增/缺陷修复/文档更新/重构/配置变更等）
        2. 明确影响范围（模块/组件/API端点）
        3. 提取关键变更点（不超过3个核心修改）
        4. 遵循约定式提交格式：<类型>[可选 范围]: <描述>\n\n[可选正文]\n\n[可选脚注]
        
        示例：
        feat(authentication): 添加JWT令牌验证功能
        \n\n        - 新增JWT生成与验证中间件
        - 集成配置项到security模块
        - 补充Swagger文档说明

        你的返回只包含提交信息，不要包含任何其他内容。
        """.strip()

    def execute_commit(self, message: str):
        try:
            subprocess.run(
                ['git', 'commit', '-m', message],
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError("提交执行失败，请检查git状态")
            
    def get_unstaged_files(self) -> List[str]:
        """获取未暂存的文件列表"""
        try:
            # 获取未跟踪的文件
            untracked_result = subprocess.run(
                ['git', 'ls-files', '--others', '--exclude-standard'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=True
            )
            
            # 获取已修改但未暂存的文件
            modified_result = subprocess.run(
                ['git', 'diff', '--name-only'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=True
            )
            
            # 合并文件列表并去重
            files = []
            if untracked_result.stdout:
                files.extend(untracked_result.stdout.strip().split('\n'))
            if modified_result.stdout:
                files.extend(modified_result.stdout.strip().split('\n'))
                
            # 过滤空字符串并去重
            return [f for f in files if f.strip()]
        except subprocess.CalledProcessError as e:
            return []
    
    def execute_add(self, files: List[str]) -> bool:
        """执行git add命令添加指定文件"""
        if not files:
            return False
            
        try:
            cmd = ['git', 'add'] + files
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"添加文件失败: {str(e)}")
    
    def execute_push(self, remote: str = 'origin', branch: str = '') -> bool:
        """执行git push命令推送到远程仓库"""
        try:
            # 如果未指定分支，获取当前分支
            if not branch:
                branch_result = subprocess.run(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    check=True
                )
                branch = branch_result.stdout.strip()
            
            # 执行push命令
            subprocess.run(
                ['git', 'push', remote, branch],
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"推送失败: {str(e)}")
            
    def execute_reset(self) -> bool:
        """执行git reset命令撤销暂存区的更改"""
        try:
            subprocess.run(
                ['git', 'reset'],
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"撤销暂存区失败: {str(e)}")
            
    def check_conflicts(self) -> Tuple[bool, List[str], Dict[str, List[str]]]:
        """检测仓库中是否存在冲突文件，并返回冲突文件列表和冲突内容
        
        Returns:
            Tuple[bool, List[str], Dict[str, List[str]]]: 
                - 是否存在冲突
                - 冲突文件列表
                - 冲突文件及其冲突代码块的字典
        """
        try:
            # 检查是否存在未合并的文件（冲突文件）
            result = subprocess.run(
                ['git', 'ls-files', '--unmerged'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=True
            )
            
            if not result.stdout.strip():
                return False, [], {}
            
            # 提取冲突文件列表
            conflict_files = set()
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    # 格式: <mode> <object> <stage> <file>
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        conflict_files.add(parts[3])
            
            conflict_files = list(conflict_files)
            
            # 获取每个冲突文件的冲突内容
            conflict_blocks = {}
            for file in conflict_files:
                try:
                    # 读取文件内容
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 提取冲突代码块
                    conflict_pattern = r'<<<<<<< .*?\n(.*?)=======\n(.*?)>>>>>>> .*?\n'
                    matches = re.finditer(conflict_pattern, content, re.DOTALL)
                    
                    blocks = []
                    for match in matches:
                        # 提取冲突的两部分内容
                        ours = match.group(1).strip()
                        theirs = match.group(2).strip()
                        blocks.append(f"<<<<<<< HEAD\n{ours}\n=======\n{theirs}\n>>>>>>> BRANCH")
                    
                    if blocks:
                        conflict_blocks[file] = blocks
                except Exception as e:
                    # 如果读取文件失败，至少记录文件名
                    conflict_blocks[file] = [f"无法读取冲突内容: {str(e)}"]
            
            return True, conflict_files, conflict_blocks
        except subprocess.CalledProcessError as e:
            # 如果git命令执行失败，假设没有冲突
            return False, [], {}
        except Exception as e:
            # 其他异常情况，假设没有冲突
            return False, [], {}