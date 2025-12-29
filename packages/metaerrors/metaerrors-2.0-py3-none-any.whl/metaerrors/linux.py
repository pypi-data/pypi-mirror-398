"""Attention!
Do not use this module if you do not know the user's target operating system!

It only works with Linux"""

import subprocess
from metaerrors.tools import dq, frmt_msg

INFO = "--info"
WARN = "--warning"
ERROR = "--error"
STD = ""

std_format = "{name}: {msg}"


def show_simple(msg: str, title: str, disable_output: bool):
    subprocess.run(["notify-send", dq(title), dq(msg)], check=True,
                         capture_output=disable_output,
                         text=disable_output
                         )


def show(msg: str, title: str, mode: str = INFO, disable_output: bool = True):
    """Displays a pop-up"""
    try:
        subprocess.run(["zenity", mode, f"--text={dq(msg)}"], check=True,
                             capture_output=disable_output,
                             text=disable_output)
    except FileNotFoundError:
        show_simple(msg, title, disable_output)


def metaraise(err: BaseException,
              title: str = "",
              frmt: str = std_format):
    """Raise Replacement"""
    msg = frmt_msg(err, frmt)
    show(msg, title, ERROR)
