# freellama/__main__.py
from .core import FreeLlama
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="FreeLlama - Free Llama-3.3-70B Chatbot")
    parser.add_argument("--mode", choices=["fast", "best"], default="fast",
                        help="Quality mode: fast (default) or best")
    parser.add_argument("--limit", type=int, default=None,
                        help="Enable memory: auto-reset after N user messages")
    parser.add_argument("--stream", action="store_true",
                        help="Show response token-by-token (streaming)")
    parser.add_argument("message", nargs="?", default=None,
                        help="Send a single message and exit")

    args = parser.parse_args()

    bot = FreeLlama(mode=args.mode, limit=args.limit, stream=args.stream)

    if args.message:
        response = bot.ask(args.message)
        if not args.stream:
            print(response)
    else:
        print(f"FreeLlama — Free Llama-3.3-70B | Mode: {args.mode.upper()} | Type 'exit' to quit\n")
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                sys.exit(0)

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break

            if user_input:
                response = bot.ask(user_input)

                if not args.stream and response:
                    print("Bot:", response)
                    print()
                elif args.stream:
                    print()  # spacing after streamed response

if __name__ == "__main__":
    main()
