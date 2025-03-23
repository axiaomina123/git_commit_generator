from git_commit_generator.config import ConfigManager
import subprocess
from typing import Optional
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
        """.strip()

    def execute_commit(self, message: str):
        try:
            subprocess.run(
                ['git', 'commit', '-m', message],
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError("提交执行失败，请检查git状态")