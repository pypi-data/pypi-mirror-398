# freellm/__main__.py
from .core import FreeLLM
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="FreeLLM - Free access to DeepSeek, Gemini, Claude & GPT via talkai.info"
    )
    parser.add_argument(
        "--model",
        choices=["deepseek", "google", "claude", "gpt"],
        default="gpt",
        help="Model: deepseek, google, claude, gpt (default)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Enable memory: max user messages before reset"
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Show response token-by-token"
    )
    parser.add_argument(
        "message",
        nargs="?",
        default=None,
        help="Send a single message and exit"
    )
    args = parser.parse_args()

    bot = FreeLLM(model=args.model, limit=args.limit, stream=args.stream)

    if args.message:
        response = bot.ask(args.message)
        if not args.stream:
            print(response)
    else:
        bot.chat()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
