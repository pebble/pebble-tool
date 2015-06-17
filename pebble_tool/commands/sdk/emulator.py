from __future__ import absolute_import
__author__ = 'katharine'

import errno
import os
import signal

from ..base import BaseCommand
import pebble_tool.sdk.emulator as emulator


class KillCommand(BaseCommand):
    command = 'kill'

    def __call__(self, args):
        if args.force:
            s = signal.SIGKILL
        else:
            s = signal.SIGTERM
        for platform in ('aplite', 'basalt'):
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
