from git_commit_generator.config import ConfigManager
from git_commit_generator.models.adapter import ModelAdapter
from git_commit_generator.git_operations import GitOperations
from typing import Optional, List, Tuple, Dict

class CommitGenerator:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.current_provider = config.get('current_provider')
        self.git = GitOperations()

    def get_staged_diff(self) -> Optional[str]:
        return self.git.get_staged_diff()

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
        return self.git.execute_commit(message)
            
    def get_unstaged_files(self) -> List[str]:
        return self.git.get_unstaged_files()
    
    def execute_add(self, files: List[str]) -> bool:
        return self.git.execute_add(files)
    
    def execute_push(self, remote: str = 'origin', branch: str = '') -> bool:
        return self.git.execute_push(remote, branch)
            
    def execute_reset(self) -> bool:
        return self.git.execute_reset()
            
    def has_staged_changes(self) -> bool:
        return self.git.has_staged_changes()
            
    def get_unpushed_commits(self) -> List[dict]:
        return self.git.get_unpushed_commits()
            
    def get_staged_files(self) -> List[str]:
        return self.git.get_staged_files()
            
    def check_conflicts(self) -> Tuple[bool, List[str], Dict[str, List[str]]]:
        return self.git.check_conflicts()