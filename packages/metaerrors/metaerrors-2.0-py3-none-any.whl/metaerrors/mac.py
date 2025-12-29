"""Attention!
Do not use this module if you do not know the user's target operating system!

It only works with macOS"""

import subprocess
from metaerrors.tools import dq, q, frmt_msg

std_format = "{name}: {msg}"
std_title = ""


def show(msg: str, title: str = std_title, disable_output: bool = True):
    """Displays a pop-up"""
    subprocess.run(["osascript", "-e",
                          q('display dialog %s buttons {\"OK\"} default button \"OK\" with title %s' % (
                              dq(msg), dq(title)))], check=True,
                         capture_output=disable_output,
                         text=disable_output
                         )


def metaraise(err: BaseException,
              title: str = "The program terminated with the error:",
              frmt: str = std_format):
    """Raise Replacement"""
    msg = frmt_msg(err, frmt)
    show(msg, title)
