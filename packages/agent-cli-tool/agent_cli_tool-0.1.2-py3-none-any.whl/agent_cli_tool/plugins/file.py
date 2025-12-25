from pathlib import Path
from re import finditer

# 正则表达式匹配 @file("file_path")
FILE_PATTERN = r"""@file\(['"]?([^'"]+?)['"]?\)"""


def get_file_content(file_path: str) -> str:
    """
    读取文件内容并返回。

    :param file_path: 文件路径
    :return: 文件内容的字符串
    :raises FileNotFoundError: 如果文件不存在或路径无效，抛出文件未找到错误
    """
    file = Path(file_path)
    if file.exists() and file.is_file():
        return file.read_text(encoding="utf-8")
    raise FileNotFoundError(f"File not exist: {file_path}")


def before_ai_ask_hook(user_input: str, mode: str) -> str:
    """
    在用户输入传递给 AI 之前，处理包含 @file("file_path") 的输入。

    :param user_input: 用户输入的字符串
    :param mode: AI模式（未使用，保留参数以备扩展）
    :return: 处理后的用户输入字符串
    """
    matches = finditer(FILE_PATTERN, user_input)
    for _match in matches:
        file_func = _match.group(0)
        file_path = _match.group(1)
        file_content = get_file_content(file_path)
        user_input = user_input.replace(file_func, file_content)
    return user_input


if __name__ == "__main__":
    user_input = 'Please descript this code: @file("plugins/file.py")'
    processed_input = before_ai_ask_hook(user_input, "default")
    print(processed_input)
