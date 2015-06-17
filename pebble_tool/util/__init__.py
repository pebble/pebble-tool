__author__ = 'katharine'

import os.path
import platform


def get_persist_dir():
    if platform.system() == 'Darwin':
        dir = os.path.expanduser("~/Library/Application Support/Pebble SDK")
    else:
        dir = os.path.expanduser("~/.pebble-sdk")
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir
