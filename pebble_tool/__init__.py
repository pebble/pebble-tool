from __future__ import absolute_import, print_function
__author__ = 'katharine'

import atexit
import argparse
import logging
import sys
import requests.packages.urllib3 as urllib3

from .commands.base import register_children
from .commands.sdk import build, create
from .commands import (install, logs, screenshot, timeline, emucontrol, ping, account, repl,
                       transcription_server, data_logging)
from .commands.sdk import manage, analyse_size, convert, emulator
from .exceptions import ToolError
from .sdk import sdk_version
from .util.analytics import wait_for_analytics, analytics_prompt
from .util.config import config
from .util.updates import wait_for_update_checks
from .version import __version__, __version_info__


def run_tool(args=None):
    urllib3.disable_warnings()  # sigh. :(
    logging.basicConfig()
    analytics_prompt()
    parser = argparse.ArgumentParser(description="Pebble Tool", prog="pebble",
                                     epilog="For help on an individual command, call that command with --help.")
    version_string = "Pebble Tool v{}".format(__version__)
    if sdk_version() is not None:
        version_string += " (active SDK: v{})".format(sdk_version())
    parser.add_argument("--version", action="version", version=version_string)
    register_children(parser)
    args = parser.parse_args(args)
    if not hasattr(args, 'func'):
        parser.error("no subcommand specified.")
    try:
        args.func(args)
    except ToolError as e:
        parser.exit(message=str(e)+"\n", status=1)
        sys.exit(1)


@atexit.register
def wait_for_cleanup():
    import time
    now = time.time()
    wait_for_analytics(2)
    wait_for_update_checks(2)
    logging.info("Spent %f seconds waiting for analytics.", time.time() - now)
    config.save()
