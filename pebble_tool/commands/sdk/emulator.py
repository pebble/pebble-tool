from __future__ import absolute_import
__author__ = 'katharine'

import errno
import os
import shutil
import signal

from ..base import BaseCommand
from pebble_tool.sdk import get_sdk_persist_dir, get_persist_dir, pebble_platforms
import pebble_tool.sdk.emulator as emulator


class KillCommand(BaseCommand):
    """Kills running emulators, if any."""
    command = 'kill'

    def __call__(self, args):
        super(KillCommand, self).__call__(args)
        if args.force:
            s = signal.SIGKILL
        else:
            s = signal.SIGTERM
        for platform in pebble_platforms:
            info = emulator.get_emulator_info(platform)
            if info is not None:
                self._kill_if_running(info['qemu']['pid'], s)
                self._kill_if_running(info['pypkjs']['pid'], s)

    @classmethod
    def _kill_if_running(cls, pid, signal_number):
        try:
            os.kill(pid, signal_number)
        except OSError as e:
            if e.errno == errno.ESRCH:
                pass

    @classmethod
    def add_parser(cls, parser):
        parser = super(KillCommand, cls).add_parser(parser)
        parser.add_argument('--force', action='store_true', help="Send the processes SIGKILL")
        return parser


class WipeCommand(BaseCommand):
    """Wipes data for running emulators. By default, only clears data for the current SDK version."""
    command = 'wipe'

    def __call__(self, args):
        super(WipeCommand, self).__call__(args)
        if args.everything:
            shutil.rmtree(get_persist_dir())
        else:
            for platform in pebble_platforms:
                shutil.rmtree(get_sdk_persist_dir(platform))

    @classmethod
    def add_parser(cls, parser):
        parser = super(WipeCommand, cls).add_parser(parser)
        parser.add_argument('--everything', action='store_true',
                            help="Deletes all data from all versions. Also logs you out.")
        return parser
