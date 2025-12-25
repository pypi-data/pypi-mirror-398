import argparse

parser = argparse.ArgumentParser(description="Ask any questions to AI")
parser.add_argument(
    "prompt",
    nargs="?",
    type=str,
    help="用户输入的 prompt",
)
parser.add_argument(
    "-m",
    "--model",
    type=str,
    help="用户选择的 AI model",
    default="",
)
parser.add_argument(
    "-a",
    "--ahead",
    action="store_false",
    help="参数 prompt 是否拼接在管道 prompt 的前面, 默认为 true",
    default=True,
)
parser.add_argument(
    "-iu",
    "--ignore_user",
    action="store_true",
    help="不输出 user 输入的 prompt, 默认为 false",
    default=False,
)
parser.add_argument(
    "-ia",
    "--ignore_ai",
    action="store_true",
    help="不输出 ai 的模型信息, 默认为 false",
    default=False,
)
parser.add_argument(
    "-it",
    "--ignore_think",
    action="store_true",
    help="不输出 ai 的思考信息, 默认为 false",
    default=False,
)
parser.add_argument(
    "-c",
    "--conversation",
    action="store_true",
    help="启用多轮对话模式, 默认为 false",
    default=False,
)
parser.add_argument(
    "-sh",
    "--shell",
    action="store_true",
    help="启用 `shell脚本` 模式, AI 只会生成 shell 脚本, 默认为 false",
    default=False,
)
parser.add_argument(
    "-co",
    "--code",
    action="store_true",
    help="启用 `code代码` 模式, AI 只会生成相关代码, 默认为 false",
    default=False,
)
parser.add_argument(
    "-o",
    "--output",
    type=str,
    help="将 AI 的输出写入指定文件",
    default="",
)
parser.add_argument(
    "-r",
    "--rich",
    action="store_true",
    help="将 AI 的输出使用 rich 进行 markdown 渲染, 默认为 false",
    default=False,
)

cli_args = parser.parse_args()
