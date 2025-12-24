"""
Demo for timed_prompt: cross-platform input()/getpass() with a real timeout.

- Shows normal usage (prompt displayed)
- Shows quiet mode usage (prompt not displayed)
"""

import os
import sys

# Add parent folder to sys.path for development mode
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from timed_prompt import timed_input_or_getpass


def demo_normal():
    """Prompt with visible message, 30s timeout"""
    print("=== Normal mode demo ===")
    pw = timed_input_or_getpass("Password (30s timeout): ", 30)
    if pw is None:
        print("Timed out")
    else:
        print(f"Password entered: {pw} (length: {len(pw)})")
    print()


def demo_quiet():
    """Prompt without visible message (quiet mode), 20s timeout"""
    print("=== Quiet mode demo ===")
    pw = timed_input_or_getpass("Enter password (quiet, 20s timeout): ", 20, quiet=True)
    if pw is None:
        print("Timed out (quiet mode)")
    else:
        print(f"Password entered (quiet mode, length): {len(pw)}")
    print()


def main():
    demo_normal()
    demo_quiet()


if __name__ == "__main__":
    main()
