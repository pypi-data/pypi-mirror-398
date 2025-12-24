import sys

import pyperclip


def copy() -> None:
    content = sys.stdin.read()
    pyperclip.copy(content)


def paste() -> None:
    print(pyperclip.paste(), end="")
