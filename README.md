# 智能Git提交工具 使用文档

## 目录

- [简介](#简介)
- [安装](#安装)
- [快速开始](#快速开始)
- [命令行工具](#命令行工具)
  - [commit 命令](#commit-命令)
  - [quick-push 命令](#quick-push-命令)
  - [config 命令](#config-命令)
- [配置管理](#配置管理)
  - [基本配置](#基本配置)
  - [AI提供商配置](#ai提供商配置)
  - [支持的AI提供商](#支持的ai提供商)
- [常见问题](#常见问题)
- [故障排除](#故障排除)

## 简介

Git Commit Generator 是一个基于AI的Git提交工具，帮助开发者快速生成规范的提交信息，并快速推送代码。该工具通过智能分析代码变更，生成规范的提交信息，提供一体化的git add、commit和push，提高开发效率。

主要特点：

- 支持多种AI服务提供商（OpenAI、Anthropic、DeepSeek等）
- 智能分析代码变更，生成规范的提交信息
- 提供一体化的git add、commit和push操作

## 安装

### 依赖项

- Python 3.7+
- Git

### 安装方法

```bash
# 使用pip安装
pip install quick-auto-git

# 或者从源码安装
git clone https://github.com/yourusername/git-commit-generator.git
cd git-commit-generator
pip install -r requirements.txt
pip install -e .
```

安装完成后，可以通过`git-ai`命令访问工具的所有功能。

## 快速开始

1. 配置AI服务提供商
使用`newpro`命令交互式添加：系统会引导你输入提供商名称、API密钥、模型名称等信息。

```bash
git-ai config newpro
```

2. 在Git仓库中使用

```bash
# 进入你的Git项目
cd your_project

# 生成提交信息并提交
git-ai commit

# 或者使用一体化命令（add、commit和push）
git-ai quick-push
```

## 命令行工具

### commit 命令

生成并提交Git commit信息。

```bash
git-ai commit [选项]
```

选项：
- `-t/--preview`: 仅生成提交信息，不执行提交操作
- `-h/--help`: 显示帮助信息

### quick-push 命令

快速完成add、commit和push操作。

```bash
git-ai quick-push [选项]
```

选项：
- `-b/--branch`: 指定分支名称
- `-r/--origin`: 指定远程仓库名称
- `-h/--help`: 显示帮助信息

### config 命令

配置管理系统，包含设置/查询/重置/添加/移除/选择配置项功能。

```bash
git-ai config [子命令] [选项]
```

子命令：
- `set`: 设置指定配置项的值
- `get`: 查询指定配置项的当前值
- `list`: 显示所有已存储的配置项
- `reset`: 清除所有配置项
- `newpro`: 交互式添加新的AI服务商配置
- `remove`: 移除指定或全部模型配置
- `select`: 选择当前使用的AI模型

## 配置管理

### 基本配置

```bash
# 列出所有配置
git-ai config list

# 设置配置项
git-ai config set <key> <value> [--provider <provider_name>]

# 获取配置项
git-ai config get <key> [--provider <provider_name>]

# 重置所有配置
git-ai config reset
```

### AI提供商配置

每个AI提供商需要配置以下项目：

- `api_key`: API密钥
- `model_name`: 模型名称
- `model_url`: API端点URL（可选，大多数提供商有默认值）
- `max_tokens`: 最大生成令牌数（可选，默认1024）

示例：

```bash
# 使用select命令交互式选择
git-ai config select

# 或直接设置current_provider
git-ai config set current_provider openai
``
# 修改指定模型配置
git-ai config set api_key sk-your-api-key -p openai
git-ai config set model_name gpt-4 -p openai
git-ai config set model_url -ai config set model_url URL_ADDRESS.openai.com/v1 -p openai
git-ai config set max_tokens 1024 -p openai
# 移除指定模型配置
git-ai config remove openai

# 列出所有模型配置
git-ai config list
```

### 支持的AI提供商

工具支持以下AI服务提供商：

| 提供商 | 提供商ID | 默认模型 | 说明 |
|-------|---------|---------|------|
| OpenAI | openai | gpt-3.5-turbo | 支持GPT-3.5和GPT-4系列模型 |
| Anthropic | anthropic | claude-3-opus-20240229 | 支持Claude系列模型 |
| DeepSeek | deepseek | deepseek-chat | 支持DeepSeek系列模型 |
| ChatGLM | chatglm | glm-4-flash | 支持ChatGLM系列模型 |
| Azure OpenAI | azure | gpt-4 | 支持Azure上的OpenAI模型 |
| Google | google | gemma | 支持Google的AI模型 |
| Baidu | baidu | ERNIE-Bot-4 | 支持百度文心一言模型 |
| Moonshot | moonshot | moonshot-v1-8k | 支持Moonshot AI模型 |
| HuggingFace | huggingface | - | 支持HuggingFace上的模型 |

## 常见问题

### Q: 如何添加新的AI提供商？

使用`newpro`命令交互式添加：

```bash
git-ai config newpro
```

系统会引导你输入提供商名称、API密钥、模型名称等信息。

### Q: 如何切换使用的AI模型？

```bash
# 使用select命令交互式选择
git-ai config select

# 或直接设置current_provider
git-ai config set current_provider anthropic
```

### Q: 提交信息生成失败怎么办？

1. 检查API密钥是否正确
2. 确认网络连接是否正常
3. 查看是否有足够的API额度
4. 尝试使用其他AI提供商

## 故障排除

### API调用失败

```bash
# 检查API配置
git-ai config get api_key --provider openai
```

### 提交操作失败

```bash
# 检查Git状态
git status

# 使用预览模式
git-ai commit -t
```

### 配置问题

```bash
# 重置配置
git-ai config reset
```
