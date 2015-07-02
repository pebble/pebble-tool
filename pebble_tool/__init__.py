from __future__ import absolute_import, print_function
__author__ = 'katharine'

import argparse
import logging
import sys

from .commands.base import register_children
from .commands import repl, install, screenshot, logs, account, timeline
from .commands.sdk import build, emulator, create, convert
from .exceptions import ToolError
from .sdk import sdk_version


def run_tool(args=None):
    logging.basicConfig()
    parser = argparse.ArgumentParser(description="Pebble Tool", prog="pebble")
    parser.add_argument("--version", action="version", version="Pebble SDK {}".format(sdk_version()))
    register_children(parser)
    args = parser.parse_args(args)
    try:
        args.func(args)
    except ToolError as e:
        print(str(e))
        sys.exit(1)
