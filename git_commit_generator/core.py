from git_commit_generator.config import ConfigManager
import subprocess
from typing import Optional, List, Tuple
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