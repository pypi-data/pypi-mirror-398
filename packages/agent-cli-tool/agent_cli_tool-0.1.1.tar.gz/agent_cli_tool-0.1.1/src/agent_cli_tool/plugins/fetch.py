from re import finditer

import requests

# 正则表达式匹配 @fetch("url")
FETCH_PATTERN = r"""@fetch\(['"]?([^'"]+?)['"]?\)"""


def get_http_content(url: str) -> str:
    """
    发送 HTTP GET 请求并返回响应内容。

    :param url: 请求的 URL
    :return: 响应内容的字符串
    :raises RuntimeError: 如果请求失败，抛出运行时错误
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        return response.text
    except Exception as e:
        raise RuntimeError(f"Failed to fetch content from {url}: {e}")


def before_ai_ask_hook(user_input: str, mode: str) -> str:
    """
    在用户输入传递给 AI 之前，处理包含 @fetch("url") 的输入。

    :param user_input: 用户输入的字符串
    :param mode: AI模式（未使用，保留参数以备扩展）
    :return: 处理后的用户输入字符串
    """
    matches = finditer(FETCH_PATTERN, user_input)
    for _match in matches:
        fetch_func = _match.group(0)
        url = _match.group(1)
        http_content = get_http_content(url)
        user_input = user_input.replace(fetch_func, http_content)
    return user_input


if __name__ == "__main__":
    user_input = 'Please fetch this content: @fetch("https://www.baidu.com")'
    processed_input = before_ai_ask_hook(user_input, "default")
    print(processed_input)
