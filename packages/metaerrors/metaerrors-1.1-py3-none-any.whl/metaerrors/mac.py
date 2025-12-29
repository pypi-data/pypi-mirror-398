"""Attention!
Do not use this module if you do not know the user's target operating system!

It only works with MacOs"""

import subprocess

std_format = "{name}: {msg}"
std_title = ""


def show(msg: str, title: str = std_title, disable_output: bool = True):
    """Displays a pop-up"""
    out = subprocess.run(["osascript", "-e",
                          "'display dialog \"%s\" buttons {\"OK\"} default button \"OK\" with title \"%s\"'" % (
                              msg, title)], check=True,
                         capture_output=disable_output,
                         text=disable_output
                         )


def metaraise(err: BaseException,
              title: str = "The program terminated with the error:",
              frmt: str = std_format):
    """Raise Replacement"""
    msg = frmt.format(msg=err.__str__(), name=err.__class__.__name__)
    show(msg, title)
