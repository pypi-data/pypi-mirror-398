#!/usr/bin/env python3
from sys import stdout

from .agents import Agent
from .cli import cli_args
from .config import env_config
from .plugins import after_ai_ask, before_ai_ask


def main():
    model = env_config.get("DEFAULT_MODEL")
    assert model, "AI model is required!"

    agent = Agent(
        cli_args,
        model,
        env_config,
        output_io=stdout,
        before_ai_ask_hook=before_ai_ask,
        after_ai_ask_hook=after_ai_ask,
    )
    try:
        agent.run()
    except KeyboardInterrupt:
        pass
    except Exception:
        from traceback import print_exc

        print_exc()


if __name__ == "__main__":
    main()
