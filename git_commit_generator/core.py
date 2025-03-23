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
        # provider_config = self.config.get('providers')[self.current_provider]
        try:
            return ModelAdapter(self.current_provider).generate(diff_content)
        except Exception as e:
            raise RuntimeError(f"API调用失败: {str(e)}")

    def execute_commit(self, message: str):
        try:
            subprocess.run(
                ['git', 'commit', '-m', message],
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError("提交执行失败，请检查git状态")