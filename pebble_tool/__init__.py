from __future__ import absolute_import, print_function
__author__ = 'katharine'

import atexit
import argparse
import logging
import sys
import requests.packages.urllib3 as urllib3

from .commands.base import register_children
from .commands.sdk import build, create
from .commands import install, logs, screenshot, timeline, ping, account, repl
from .commands.sdk import analyse_size, convert, emulator
from .exceptions import ToolError
from .sdk import sdk_version
from .util.analytics import wait_for_analytics, analytics_prompt


def run_tool(args=None):
    urllib3.disable_warnings()  # sigh. :(
    logging.basicConfig()
    analytics_prompt()
    parser = argparse.ArgumentParser(description="Pebble Tool", prog="pebble")
    parser.add_argument("--version", action="version", version="Pebble SDK {}".format(sdk_version()))
    parser.add_argument("--waf", help="A string containing arguments to pass directly to Waf")
    register_children(parser)
    args, unknown = parser.parse_known_args(args)
    args.waf = args.waf.split() if args.waf else []
    args.waf.extend(unknown)

    if not hasattr(args, 'func'):
        parser.error("no subcommand specified.")
    try:
        args.func(args)
    except ToolError as e:
        parser.exit(message=str(e), status=1)
        sys.exit(1)


@atexit.register
def wait_for_cleanup():
    import time
    now = time.time()
    wait_for_analytics(2)
    logging.info("Spent %f seconds waiting for analytics.", time.time() - now)
