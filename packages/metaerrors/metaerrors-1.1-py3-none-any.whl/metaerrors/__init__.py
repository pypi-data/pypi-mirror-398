"""This library redirects errors to popups

This library is supported for Windows, Linux, and macOS.

Constants indicate the popup type, and std_title and msg_format indicate the standard title and message format.
Example of the message format: {name}: {msg}"""

import sys

import metaerrors.linux
import metaerrors.mac
import metaerrors.win

INFO = 0
WARN = 1
ERROR = 2
STD = 3

std_title = "The program terminated with the error:"
msg_format = "{name}: {msg}"

win_types = [win.INFO, win.WARN, win.ERROR, win.STD]
linux_types = [linux.INFO, linux.WARN, linux.ERROR, linux.STD]

is_win = sys.platform.startswith("win")
is_linux = sys.platform.startswith("linux")
is_mac = sys.platform.startswith("darwin")
is_not_support = not (is_win or is_linux or is_mac)


def show(msg: str, title: str, mode: int):
    """Displays a pop-up"""
    if is_win:
        md = win_types[mode]
        win.show(msg, title, md)
    elif is_linux:
        md = linux_types[mode]
        linux.show(msg, title, md)
    elif is_mac:
        mac.show(msg, title)
    else:
        raise OSError("Your operating system is not supported.")


def metaraise(err: BaseException, title: str = std_title, frmt: str = msg_format, do_exit: bool = False):
    """Raise Replacement"""
    if is_win:
        win.metaraise(err, title, frmt)
    elif is_linux:
        linux.metaraise(err, title, frmt)
    elif is_mac:
        mac.metaraise(err, title, frmt)
    else:
        raise err
    if do_exit: sys.exit(1)
