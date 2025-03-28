# 智能Git提交工具使用说明

## 一、环境准备
```bash
# 安装依赖（Windows系统）
pip install -r d:\jobFiles\gptcomet-master\git_commit_generator\requirements.txt
```

## 二、快速入门
1. 初始化配置（首次使用）
```bash
git-ai config --set api.key=your_api_key
git-ai config --set model.provider=deepseek
```

2. 基础使用流程
```bash
# 进入git仓库目录
cd your_project

# 执行智能提交
git-ai push
```

## 三、核心功能详解

### 1. 语言切换功能
```bash
# 设置为英文界面（支持zh_CN/en_JP等）
git-ai --lang en_US push
```
![示意图：语言切换效果](data:image/png;base64,...)

### 2. 配置管理系统
```python:d:\jobFiles\gptcomet-master\git_commit_generator\config.py
# 配置文件示例内容：
[model]
provider = deepseek
temperature = 0.7

[security]
confirm_timeout = 10
```

常用配置命令：
```bash
# 查看所有配置
git-ai config --list

# 设置OpenAI配置
git-ai config --set openai.model=gpt-4
```

### 3. 模型切换示例
```bash
# 切换为Google模型
git-ai config --set model.provider=google
git-ai config --set google.project=your-project-123
```

### 4. 智能提交流程
完整执行流程：
1. 自动检测git status
2. 生成diff对比文件
3. 调用AI模型生成建议
4. 进入编辑界面（vim/nano）
5. 确认后执行完整提交

![流程图](data:image/png;base64,...)

## 四、安全机制说明

### 1. 双重确认机制
```python:d:\jobFiles\gptcomet-master\git_commit_generator\safety.py
# 关键操作前提示
Are you sure to push to 'main' branch? [y/N]
```

### 2. 应急措施
```bash
# 使用安全模式（不实际执行操作）
git-ai push --dry-run

# 回退上次提交
git-ai undo --last-commit
```

## 五、高级功能指南

### 1. 自定义提交模板
```bash
# 设置自定义提示词
git-ai config --set prompt.template="请用中文生成简洁的提交说明，包含以下要素：\n1. 变更类型\n2. 影响范围"

# 查看生成的提示词
git-ai debug --show-prompt
```

### 2. 多仓库配置
```bash
# 为特定仓库设置独立配置
cd project-A
git-ai config --local model.provider=openai
```

## 六、常见问题处理

### 1. 报错处理指南
| 错误现象 | 解决方案 |
|---------|---------|
| API连接失败 | 检查网络或重试3次 |
| 生成内容过长 | 设置max_tokens=500 |
| 中文乱码 | 设置LANG=zh_CN.UTF-8 |

### 2. 性能优化建议
```bash
# 启用本地缓存
git-ai config --set cache.enabled=true

# 限制diff大小（单位KB）
git-ai config --set safety.max_diff_size=2048
```

## 七、卸载清理
```bash
# 移除配置文件
rm ~/.gitcommitrc

# 清理python包
pip uninstall git-commit-generator
```