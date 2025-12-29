"""Module for FreeBSD based on metaerrors.linux

Attention!
Do not use this module if you do not know the user's target operating system!

It only works with FreeBSD"""

import subprocess

import metaerrors.linux as base
from metaerrors.linux import INFO, WARN, ERROR, STD, std_format
from metaerrors.tools import dq, frmt_msg

def show_xmessage(msg: str, disable_output: bool = True):
    subprocess.run(["xmessage", dq(msg)], check=True,
                   capture_output=disable_output,
                   text=disable_output)

def show(msg: str, title: str, mode: str = INFO, disable_output: bool = True):
    """Displays a pop-up"""
    try:
        base.show(msg, title, mode, disable_output)
    except FileNotFoundError:
        show_xmessage(msg, disable_output)

def metaraise(err: BaseException,
              title: str = "",
              frmt: str = std_format):
    """Raise Replacement"""
    msg = frmt_msg(err, frmt)
    show(msg, title, ERROR)

