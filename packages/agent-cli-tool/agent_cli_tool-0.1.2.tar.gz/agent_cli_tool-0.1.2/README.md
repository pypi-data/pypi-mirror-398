# Agent CLI Tool

[![PyPI version](https://badge.fury.io/py/agent-cli-tool.svg)](https://badge.fury.io/py/agent-cli-tool)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful command-line tool for interacting with AI models (OpenAI, DeepSeek, Claude) directly from your terminal.

## Features

- 🚀 Support for multiple AI models (GPT-4o, DeepSeek, Claude)
- 💬 Interactive conversation mode
- 💻 Shell script generation mode
- 📝 Code generation mode
- 🎨 Rich markdown output formatting
- 📂 Output redirection to files
- ⚙️ Configurable via environment variables
- 🧩 Plugin system with built-in plugins:
  - `file`: Insert file content using `@file("path/to/file")` syntax
  - `fetch`: Insert web content using `@fetch("url")` syntax
  - `shell`: Interactive shell command execution confirmation

## Installation

### Using pip

```bash
pip install agent-cli-tool
```

### Using uv

```bash
uv tool install agent-cli-tool
```

### From source

1. Clone the repository:
```bash
git clone https://github.com/Awoodwhale/agent-cli-tool.git
cd agent-cli-tool
```

2. Install with uv:
```bash
uv pip install -e .
```

## Configuration

Create a `.env` file in your project directory with the following variables:

```ini
API_KEY=your_api_key
BASE_URL=your_api_base_url  # Optional
DEFAULT_MODEL=deepseek-chat  # DeepSeek Chat by default
```

## Usage

### Basic query

```bash
agent-cli-tool "Tell me about AI"
```

### Shell mode (generates shell commands only)

```bash
agent-cli-tool "how to list all python processes" --shell
```

### Code mode (generates code only)

```bash
agent-cli-tool "python fibonacci function" --code
```

### Conversation mode

```bash
agent-cli-tool --conversation
agent-cli-tool -c
```

### Using different models

```bash
agent-cli-tool "Explain quantum computing" -m 4O  # GPT-4o
agent-cli-tool "Solve this math problem" -m R1    # DeepSeek Reasoner
agent-cli-tool "Write a poem" -m claude           # Claude
```

### Rich output formatting

```bash
agent-cli-tool "Explain machine learning" --rich
```

### Output to file

```bash
agent-cli-tool "Generate python code for web scraper" --code --output scraper.py
```

## Command Line Options

```
usage: agent-cli-tool [-h] [-m MODEL] [-a] [-iu] [-ia] [-it] [-c] [-sh] [-co] [-o OUTPUT] [-r] [prompt]

Ask any questions to AI

positional arguments:
  prompt                用户输入的 prompt

options:
  -h, --help            show this help message and exit
  -m MODEL, --model MODEL
                        用户选择的 AI model
  -a, --ahead          参数 prompt 是否拼接在管道 prompt 的前面, 默认为 true
  -iu, --ignore_user    不输出 user 输入的 prompt, 默认为 false
  -ia, --ignore_ai      不输出 ai 的模型信息, 默认为 false
  -it, --ignore_think   不输出 ai 的思考信息, 默认为 false
  -c, --conversation    启用多轮对话模式, 默认为 false
  -sh, --shell          启用 `shell脚本` 模式, AI 只会生成 shell 脚本, 默认为 false
  -co, --code           启用 `code代码` 模式, AI 只会生成相关代码, 默认为 false
  -o OUTPUT, --output OUTPUT
                        将 AI 的输出写入指定文件
  -r, --rich            将 AI 的输出使用 rich 进行 markdown 渲染, 默认为 false
```

## Supported Models

| Short Name | Model Name                  | Description                |
|------------|-----------------------------|----------------------------|
| chatgpt    | gpt-4o                      | OpenAI GPT-4o              |
| 4O         | gpt-4o                      | OpenAI GPT-4o              |
| V3         | deepseek-chat               | DeepSeek Chat              |
| R1         | deepseek-reasoner           | DeepSeek Reasoner          |
| claude     | claude-3-7-sonnet-20250219  | Claude 3 Sonnet            |

## Development

### Project Structure

```
.
├── src
│   └── agent_cli_tool
│       ├── agents/          # AI agent implementations
│       ├── cli/             # Command line interface
│       ├── config/          # Configuration handling
│       └── plugins/         # Plugin system
│           ├── __init__.py  # Plugin loader and interfaces
│           ├── fetch.py     # Fetch web content plugin
│           ├── file.py      # File content injection plugin
│           └── shell.py     # Shell command execution plugin
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

### Dependencies

Core dependencies:
- openai>=1.75.0
- python-dotenv>=1.1.0
- requests>=2.32.3
- rich>=14.0.0

## License

MIT