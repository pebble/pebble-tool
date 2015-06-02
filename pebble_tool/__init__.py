__author__ = 'katharine'

import argparse

from .commands.base import register_children
from .commands import repl, install
from .exceptions import ToolError


def run_tool(args=None):
    parser = argparse.ArgumentParser()
    register_children(parser)
    args = parser.parse_args(args)
    try:
        args.func(args)
    except ToolError as e:
        print str(e)
