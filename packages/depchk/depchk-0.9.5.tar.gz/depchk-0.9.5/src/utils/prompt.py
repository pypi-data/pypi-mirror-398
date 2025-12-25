import sys
from typing import Any

from chalkbox.logging.bridge import get_logger

logger = get_logger(__name__)


class PromptHandler:
    @staticmethod
    def prompt_with_fallback(prompt_dict: dict[str, Any], default_action: str = "continue") -> bool:
        print("\n" + "=" * 60)
        print("! Python Version Mismatch Detected")
        print("=" * 60)
        print(f"Main project:          Python {prompt_dict['main_python']}")
        print(f"Local dependency req:  Python {prompt_dict['vendor_python']}")
        if "details" in prompt_dict:
            print(f"\n{prompt_dict['details']}")

        try:
            if not sys.stdin.isatty():
                logger.debug("Non-interactive environment, proceeding automatically")
                print("\n! No terminal available, proceeding with Python version mismatch...")
                return True

            print(
                prompt_dict.get("prompt", "\nDo you want to proceed? (y/n): "), end="", flush=True
            )

            try:
                with open("/dev/tty") as tty:
                    response = tty.readline().strip()
                    return response.lower() == "y"
            except (OSError, FileNotFoundError) as e:
                logger.debug(f"TTY error: {type(e).__name__}: {e}")
                response = input().strip()
                return response.lower() == "y"

        except (EOFError, KeyboardInterrupt):
            logger.debug("User interrupted prompt")
            return default_action == "continue"
