"""Attention!
Do not use this module if you do not know the user's target operating system!

It only works with Linux"""

import subprocess

INFO = "--info"
WARN = "--warning"
ERROR = "--error"
STD = ""

std_format = "{name}: {msg}"


def show_simple(msg: str, title: str, disable_output: bool):
    out = subprocess.run(["notify-send", title, msg], check=True,
                         capture_output=disable_output,
                         text=disable_output
                         )


def show(msg: str, title: str, mode: str = INFO, disable_output: bool = True):
    """Displays a pop-up"""
    try:
        out = subprocess.run(["zenity", mode, f"--text={msg}"], check=True,
                             capture_output=disable_output,
                             text=disable_output)
    except FileNotFoundError:
        show_simple(msg, title, disable_output)


def metaraise(err: BaseException,
              title: str = "",
              frmt: str = std_format):
    """Raise Replacement"""
    msg = frmt.format(msg=err.__str__(), name=err.__class__.__name__)
    show(msg, title, ERROR)
