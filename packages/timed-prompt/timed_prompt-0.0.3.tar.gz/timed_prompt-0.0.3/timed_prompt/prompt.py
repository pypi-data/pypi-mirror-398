__version__ = "2025.12.21.01"
__author__ = "Muthukumar Subramanian"

"""
timed_input.prompt

Cross-platform input/getpass prompt with real timeout.
Supports Windows, Linux, and macOS.
"""

import sys
import subprocess


def timed_input_or_getpass(prompt: str, timeout: float, *, quiet: bool = False):
    """
    Cross-platform input/getpass prompt with a real timeout.

    - Works on Windows, Linux, macOS
    - Uses a child Python process so blocking input()/getpass()
      can be safely terminated on timeout
    - If quiet=True, does not print the prompt (caller handles output)

    Returns:
        str | None
    """
    # Show prompt immediately unless quiet
    if not quiet:
        print(prompt, end='', flush=True)

    code = r"""
import sys
try:
    s = input()
except EOFError:
    from getpass import getpass
    s = getpass('')
print(s)
"""

    try:
        p = subprocess.run(
            [sys.executable, "-c", code],
            timeout=timeout,
            text=True,
            stdin=sys.stdin,  # inherit console input explicitly
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=False  # critical for Windows console inheritance
        )

        if not quiet:
            print()  # keep console tidy after Enter

        out = p.stdout.rstrip("\n")
        return out if out else None

    except subprocess.TimeoutExpired:
        if not quiet:
            print("\n[!] Input timed out and was canceled.")
        return None

    except KeyboardInterrupt:
        if not quiet:
            print("\n[!] Input canceled via Ctrl+C.")
        return None
