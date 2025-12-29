"""This library redirects errors to popups

This library is supported for Windows, Linux, macOS and FreeBSD.

Constants indicate the popup type, and std_title and msg_format indicate the standard title and message format.
Example of the message format: {name}: {msg}"""

import sys

import metaerrors.linux
import metaerrors.mac
import metaerrors.win
import metaerrors.freebsd

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
is_freebsd = sys.platform.startswith("freebsd")


def show(msg: str, title: str, mode: int):
    """Displays a pop-up"""
    try:
        if is_win:
            md = win_types[mode]
            win.show(msg, title, md)
        elif is_linux:
            md = linux_types[mode]
            linux.show(msg, title, md)
        elif is_mac:
            mac.show(msg, title)
        elif is_freebsd:
            md = linux_types[mode]
            freebsd.show(msg, title, md)
        else:
            raise OSError("Your operating system is not supported.")
    except OSError as e:
        raise e
    except Exception as e:
        print("[metaerrors]: Error displaying popup:", file=sys.stderr)
        raise e


def metaraise(err: BaseException, title: str = std_title, frmt: str = msg_format, do_exit: bool = False):
    """Raise Replacement"""
    try:
        if is_win:
            win.metaraise(err, title, frmt)
        elif is_linux:
            linux.metaraise(err, title, frmt)
        elif is_mac:
            mac.metaraise(err, title, frmt)
        elif is_freebsd:
            freebsd.metaraise(err, title, frmt)
        else:
            print("[metaerrors] cant display popup: OS is not supported", file=sys.stderr)
            raise err
        if do_exit: sys.exit(1)
    except Exception as e:
        if e != err: print("[metaerrors]: Error displaying exception popup:", file=sys.stderr)
        raise e

