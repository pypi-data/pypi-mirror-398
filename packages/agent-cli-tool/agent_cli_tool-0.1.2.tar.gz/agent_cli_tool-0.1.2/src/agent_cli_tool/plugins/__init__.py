__all__ = ["before_ai_ask", "after_ai_ask"]

import importlib
from pathlib import Path
from typing import Callable, List, Tuple

_before_ai_ask_hooks = []
_after_ai_ask_hooks = []


def _load_plugins(directory: Path) -> Tuple[List[Callable], List[Callable]]:
    """
    加载指定目录中的所有插件，并返回插件处理函数的列表。

    Args:
        directory (Path): 插件所在的目录路径。

    Returns:
        Tuple[List[Callable], List[Callable]]: 返回两个列表，分别包含所有 `before_ai_ask_hook` 和 `after_ai_ask_hook` 函数。
    """
    before_ai_ask_hooks = []
    after_ai_ask_hooks = []

    for plugin_file in directory.glob("*.py"):
        if plugin_file.name == "__init__.py":
            continue

        module_name = plugin_file.stem
        try:
            spec = importlib.util.spec_from_file_location(
                module_name, str(plugin_file.absolute())
            )
            if spec is None:
                continue

            plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin_module)

            if hasattr(plugin_module, "before_ai_ask_hook"):
                before_ai_ask_hooks.append(plugin_module.before_ai_ask_hook)
            if hasattr(plugin_module, "after_ai_ask_hook"):
                after_ai_ask_hooks.append(plugin_module.after_ai_ask_hook)
        except Exception as e:
            print(f"\033[1;31mError loading plugin {module_name}: {e}\033[0m")

    return before_ai_ask_hooks, after_ai_ask_hooks


_before_ai_ask_hooks, _after_ai_ask_hooks = _load_plugins(Path(__file__).parent)


def before_ai_ask(user_input: str, mode: str = "default") -> str:
    """
    在 AI 提问之前执行所有 `before_ai_ask_hook` 函数。

    Args:
        user_input (str): 用户输入的内容。
        mode (str): 模式参数，默认为 "default"。

    Returns:
        str: 经过所有钩子函数处理后的用户输入。
    """
    for hook in _before_ai_ask_hooks:
        try:
            user_input = hook(user_input, mode)
        except Exception as e:
            print(
                f"\033[1;31mError executing plugin({hook.__module__}).before_ai_ask_hook: {e}\033[0m"
            )
            exit(1)
    return user_input


def after_ai_ask(ai_reply: str, mode: str = "default") -> str:
    """
    在 AI 回答之后执行所有 `after_ai_ask_hook` 函数。

    Args:
        ai_reply (str): AI 的回复内容。
        mode (str): 模式参数，默认为 "default"。

    Returns:
        str: 经过所有钩子函数处理后的 AI 回复。
    """
    for hook in _after_ai_ask_hooks:
        try:
            ai_reply = hook(ai_reply, mode)
        except Exception as e:
            print(
                f"\033[1;31mError executing plugin({hook.__module__}).after_ai_ask_hook: {e}\033[0m"
            )
            exit(1)
    return ai_reply
