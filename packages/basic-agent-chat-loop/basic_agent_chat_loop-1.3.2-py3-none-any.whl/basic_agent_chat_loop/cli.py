"""CLI entry point for Basic Agent Chat Loop."""

import sys

from .chat_loop import main as chat_loop_main


def main():
    """Main CLI entry point."""
    return chat_loop_main()


if __name__ == "__main__":
    sys.exit(main())
