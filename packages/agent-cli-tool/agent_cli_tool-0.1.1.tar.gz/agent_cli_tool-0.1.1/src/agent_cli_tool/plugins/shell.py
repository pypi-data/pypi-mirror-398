def after_ai_ask_hook(ai_reply: str, mode: str) -> str:
    """
    根据模式决定是否执行 AI 返回的命令。

    Args:
        ai_reply (str): AI 返回的命令或回复。
        mode (str): 当前模式，只有为 "shell" 时才会执行命令。

    Returns:
        str: 返回 AI 的原始回复。
    """
    # 如果模式不是 "shell"，直接返回 AI 的回复
    if mode != "shell":
        return ai_reply

    from os import system

    # 提示用户是否执行命令
    prompt = "[E]xecute/[A]bort ([Y]es/[N]o): "
    print(f"\033[1;32m{prompt}\033[0m", end="", flush=True)

    # 获取用户输入并处理
    if input().strip().lower() in ["e", "y"]:
        # 如果用户选择执行，调用系统命令
        system(ai_reply)

    # 返回 AI 的原始回复
    return ai_reply


if __name__ == "__main__":
    ai_reply = "echo Hello, World!"
    mode = "shell"
    print(f"AI Reply: {ai_reply}")
    print(f"Mode: {mode}")
    print("Expected: Command should be executed and 'Hello, World!' should be printed.")
    result = after_ai_ask_hook(ai_reply, mode)
    print(f"Result: {result}")
