import logging
import requests

from agent import run_agent
from config import (
    DEFAULT_MODELS,
    MAX_AGENT_ITERATIONS,
    OLLAMA_API_URL,
    OLLAMA_TIMEOUT,
    SEARCH_MAX_RESULTS,
    TESSERACT_PATH,
    TRUNCATION_LIMITS,
    WORKSPACE_DIR
)

# logging configuration
logger = logging.getLogger(__name__)


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

def print_config() -> None:
    """Display safe, non-secret application configuration."""
    print(
        f"""
Configuration:
  Workspace: {WORKSPACE_DIR}
  Ollama URL: {OLLAMA_API_URL}
  Ollama timeout: {OLLAMA_TIMEOUT} seconds
  Planner model: {DEFAULT_MODELS["planner"]}
  Text model: {DEFAULT_MODELS["text"]}
  Vision model: {DEFAULT_MODELS["vision"]}
  Max agent iterations: {MAX_AGENT_ITERATIONS}
  Search result limit: {SEARCH_MAX_RESULTS}
  File truncation limit: {TRUNCATION_LIMITS["file"]}
  PDF truncation limit: {TRUNCATION_LIMITS["pdf"]}
  OCR truncation limit: {TRUNCATION_LIMITS["ocr"]}
  Tesseract path: {TESSERACT_PATH}
"""
    )


def main() -> None:
    """Run the interactive assistant loop."""
    print("ΛIgent - Local AI Agent")
    print("Connected tools are available through the agent.")
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

        if user_input == "/config":
            print_config()
            continue

        if user_input.startswith("/"):
            print(f"Unknown command: {user_input}")
            print("Type /help to see available commands.")
            continue

        try:
            print("\nWorking...")
            response = run_agent(user_input)
            print(f"\nAssistant: {response}")
        except requests.ConnectionError:
            logger.exception("Could not connect to Ollama")
            print(
                "\nError: Could not connect to Ollama. "
                "Make sure Ollama is running and try again."
            )
        except requests.Timeout:
            logger.exception("Ollama request timed out")
            print(
                "\nError: Ollama took too long to respond. "
                "Try increasing OLLAMA_TIMEOUT or using a smaller model."
            )
        except requests.HTTPError as error:
            logger.exception("Ollama returned an HTTP error")
            print(f"\nError: Ollama returned an HTTP error: {error}")
        except RuntimeError as error:
            logger.exception("Ollama returned an unexpected response")
            print(f"\nError: {error}")
        except Exception:
            logger.exception("Unexpected agent failure")
            print(
                "\nError: An unexpected error occurred. "
                "Check the logs for details."
            )

if __name__ == "__main__":
    main()