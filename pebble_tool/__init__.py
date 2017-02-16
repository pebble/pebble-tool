from __future__ import absolute_import, print_function
__author__ = 'katharine'

import atexit
import argparse
import logging
import sys
import requests.packages.urllib3 as urllib3

from .exceptions import ToolError
from .sdk import sdk_version
from .util.config import config
from .util.updates import wait_for_update_checks
from .util.wsl import maybe_apply_wsl_hacks
from .version import __version__, __version_info__

# Violating PEP8 for custom command ordering for `pebble -h`
from .commands.sdk import manage
from .commands.sdk.project import build

from .commands.base import register_children
from .commands import (install, logs, screenshot, timeline, emucontrol, ping, account, repl,
                       transcription_server, data_logging)
from .commands.sdk import create, emulator
from .commands.sdk.project import package, analyse_size, convert, debug

def run_tool(args=None):
    urllib3.disable_warnings()  # sigh. :(
    logging.basicConfig()
    maybe_apply_wsl_hacks()
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
        parser.exit(message=unicode(e)+"\n", status=1)
        sys.exit(1)


@atexit.register
def wait_for_cleanup():
    wait_for_update_checks(2)
    config.save()
