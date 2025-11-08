"""Plugins interacting with operating system applications."""

import os


def open_notepad() -> None:
    """Megnyitja a Jegyzettömb alkalmazást a Windowson."""
    os.system("notepad.exe")
