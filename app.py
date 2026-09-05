from agent import run_agent


def print_help() -> None:
    """Display available CLI commands."""
    print(
        """
Commands:
  /help    Show this help message
  /config  Show current configuration
  /exit    Exit the application
"""
    )


def main() -> None:
    """Run the interactive assistant loop."""
    print("local-slm assistant")
    print("Type /help for commands or /exit to quit.")

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            print("Please enter a request.")
            continue

        if user_input in {"/exit", "/quit"}:
            print("Goodbye.")
            break

        if user_input == "/help":
            print_help()
            continue

        if user_input.startswith("/"):
            print(f"Unknown command: {user_input}")
            print("Type /help to see available commands.")
            continue

        try:
            response = run_agent(user_input)
            print(f"\nAssistant: {response}")
        except Exception as error:
            print(f"\nError: {error}")


if __name__ == "__main__":
    main()