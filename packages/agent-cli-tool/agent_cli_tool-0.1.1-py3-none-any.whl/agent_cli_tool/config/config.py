from dotenv import dotenv_values
from pathlib import Path

# 加载配置文件
config_file = Path.home() / ".config" / "agent-cli-tool.env"
env_config = dotenv_values(
    stream=config_file.open("r", encoding="utf-8") if config_file.exists() else None
)

assert env_config, (
    f"environment config not found, please edit your config file: {config_file.absolute()}"
)

DEFAULT_PROMPT = "你是帮用户解决问题的AI,所有回复使用中文"
SHELL_PROMPT = """Provide only `{shell} `commands for `{os}` without any description.
If there is a lack of details, provide most logical solution.
Ensure the output is a valid shell command.
If multiple steps required try to combine them together using &&.
Provide only plain text without Markdown formatting.
Do not provide markdown formatting such as ``` or ```bash ."""
CODE_PROMPT = """Provide only code as output without any description.
Provide only code in plain text format without Markdown formatting.
Do not include symbols such as ``` or ```python.
If there is a lack of details, provide most logical solution.
The default code language is '{DEFAULT_LANGUAGE}'.
You are not allowed to ask for more details.
For example if the prompt is 'Hello world with Python', you should return 'print(\"Hello world\")'"""

defalut_config = {
    "DEFAULT_PROMPT": DEFAULT_PROMPT,
    "SHELL_PROMPT": SHELL_PROMPT,
    "DEFAULT_LANGUAGE": "python3",
    "CODE_PROMPT": CODE_PROMPT,
    "STREAM": "true",
    "DEFAULT_MODEL": "deepseek-chat",
    "RICH_STYLE": "github-dark",  # https://pygments.org/styles/
}

for key in defalut_config:
    if key not in env_config:
        env_config[key] = defalut_config[key]

env_config["CODE_PROMPT"] = env_config["CODE_PROMPT"].format(
    DEFAULT_LANGUAGE=env_config["DEFAULT_LANGUAGE"]
)
