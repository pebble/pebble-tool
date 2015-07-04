from __future__ import absolute_import, print_function
__author__ = 'katharine'

import argparse
import logging
import sys
import requests.packages.urllib3 as urllib3

from .commands.base import register_children
from .commands.sdk import build, create
from .commands import install, logs, screenshot, timeline, ping, account, repl
from .commands.sdk import convert, emulator
from .exceptions import ToolError
from .sdk import sdk_version


def run_tool(args=None):
    urllib3.disable_warnings()  # sigh. :(
    logging.basicConfig()
    parser = argparse.ArgumentParser(description="Pebble Tool", prog="pebble")
    parser.add_argument("--version", action="version", version="Pebble SDK {}".format(sdk_version()))
    register_children(parser)
    args = parser.parse_args(args)
    if not hasattr(args, 'func'):
        parser.error("no subcommand specified.")
    try:
        args.func(args)
    except ToolError as e:
        parser.exit(message=str(e), status=1)
        sys.exit(1)
