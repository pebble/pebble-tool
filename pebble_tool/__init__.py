__author__ = 'katharine'

import argparse
import logging

from .commands.base import register_children
from .commands import repl, install, screenshot, logs
from .commands.sdk import build, emulator
from .exceptions import ToolError


def run_tool(args=None):
    logging.basicConfig()
    parser = argparse.ArgumentParser()
    register_children(parser)
    args = parser.parse_args(args)
    try:
        args.func(args)
    except ToolError as e:
        print str(e)
