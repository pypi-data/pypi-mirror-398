# -*- coding: utf-8 -*-

"""
Definition of constants and helper functions shared by all scripts
"""

import os
import sys


# Singleton decorator definition
def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


@singleton
class GlobalParams:
    def __init__(self):
        self.logger = None
        self.this_script = None
        self.verbose = False
        self.windows = None


def check_os():
    global_params = GlobalParams()
    if os.name == "nt":
        global_params.windows = True


def debug(msg):
    global_params = GlobalParams()
    if global_params.logger:
        global_params.logger.debug("{}".format(msg))
    elif global_params.verbose:
        print(msg)


def exception_handler(exception_type, exception, traceback, debug_hook=sys.excepthook):
    global_params = GlobalParams()
    if global_params.verbose:
        debug_hook(exception_type, exception, traceback)
    else:
        print("{}: {} (use --verbose for details)".format(exception_type.__name__, exception))


def info(msg):
    global_params = GlobalParams()
    if global_params.logger:
        global_params.logger.info("{}".format(msg))
    else:
        print(msg)


def is_windows():
    global_params = GlobalParams()
    if global_params.windows is None:
        check_os()
    return global_params.windows
