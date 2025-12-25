# Agent CLI 工具

[![PyPI 版本](https://badge.fury.io/py/agent-cli-tool.svg)](https://badge.fury.io/py/agent-cli-tool)
[![许可证: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个强大的命令行工具，可直接在终端中与AI模型(OpenAI、DeepSeek、Claude)交互。

## 功能特性

- 🚀 支持多种AI模型(GPT-4o、DeepSeek、Claude)
- 💬 交互式对话模式
- 💻 Shell脚本生成模式
- 📝 代码生成模式
- 🎨 精美的Markdown输出格式
- 📂 输出重定向到文件
- ⚙️ 可通过环境变量配置
- 🧩 插件系统，内置插件:
  - `file`: 使用`@file("文件路径")`语法插入文件内容
  - `fetch`: 使用`@fetch("URL")`语法插入网页内容
  - `shell`: 交互式shell命令执行确认

## 安装指南

### 使用pip安装

```bash
pip install agent-cli-tool
```

### 使用uv安装

```bash
uv tool install agent-cli-tool
```

### 从源码安装

1. 克隆仓库：
```bash
git clone https://github.com/Awoodwhale/agent-cli-tool.git
cd agent-cli-tool
```

2. 使用uv安装：
```bash
uv pip install -e .
```

## 配置说明

在项目目录下创建`.env`文件，包含以下变量：

```ini
API_KEY=你的API密钥
BASE_URL=API URL  # 可选
DEFAULT_MODEL=deepseek-chat  # 默认为DeepSeek Chat
```

## 使用说明

### 基础查询

```bash
agent-cli-tool "告诉我关于AI的知识"
```

### Shell模式(仅生成shell命令)

```bash
agent-cli-tool "如何列出所有Python进程" --shell
```

### 代码模式(仅生成代码)

```bash
agent-cli-tool "Python斐波那契函数" --code
```

### 对话模式

```bash
agent-cli-tool --conversation
```

### 使用不同模型

```bash
agent-cli-tool "解释量子计算" -m 4O  # GPT-4o
agent-cli-tool "解决这个数学问题" -m R1    # DeepSeek Reasoner
agent-cli-tool "写一首诗" -m claude           # Claude
```

### 精美输出格式

```bash
agent-cli-tool "解释机器学习" --rich
```

### 输出到文件

```bash
agent-cli-tool "生成网页爬虫Python代码" --code --output scraper.py
```

## 命令行选项

```
usage: agent-cli-tool [-h] [-m MODEL] [-a] [-iu] [-ia] [-it] [-c] [-sh] [-co] [-o OUTPUT] [-r] [prompt]

向AI提问任何问题

位置参数:
  prompt                用户输入的提示词

选项:
  -h, --help            显示帮助信息
  -m MODEL, --model MODEL
                        选择AI模型
  -a, --ahead           提示词是否拼接在管道输入前，默认为true
  -iu, --ignore_user    不显示用户输入的提示词，默认为false
  -ia, --ignore_ai      不显示AI模型信息，默认为false
  -it, --ignore_think   不显示AI思考过程，默认为false
  -c, --conversation    启用多轮对话模式，默认为false
  -sh, --shell          启用shell脚本模式，AI只生成shell命令，默认为false
  -co, --code           启用代码模式，AI只生成相关代码，默认为false
  -o OUTPUT, --output OUTPUT
                        将AI输出写入指定文件
  -r, --rich            使用rich渲染markdown输出，默认为false
```

## 支持的模型

| 简称      | 模型名称                  | 描述                |
|-----------|---------------------------|---------------------|
| chatgpt   | gpt-4o                    | OpenAI GPT-4o       |
| 4O        | gpt-4o                    | OpenAI GPT-4o       |
| V3        | deepseek-chat             | DeepSeek Chat       |
| R1        | deepseek-reasoner         | DeepSeek Reasoner   |
| claude    | claude-3-7-sonnet-20250219| Claude 3 Sonnet     |

## 项目结构

```
.
├── src
│   └── agent_cli_tool
│       ├── agents/          # AI代理实现
│       ├── cli/             # 命令行接口
│       ├── config/          # 配置处理
│       └── plugins/         # 插件系统
│           ├── __init__.py  # 插件加载器和接口
│           ├── fetch.py     # 网页内容获取插件
│           ├── file.py      # 文件内容插入插件
│           └── shell.py     # Shell命令执行插件
├── pyproject.toml           # 项目配置
└── README.md                # 说明文档
```

## 依赖项

核心依赖:
- openai>=1.75.0
- python-dotenv>=1.1.0
- requests>=2.32.3
- rich>=14.0.0

## 许可证

MIT