from __future__ import absolute_import
__author__ = 'katharine'

import time

from .base import BaseCommand
from pebble_tool.util.logs import PebbleLogPrinter


class LogsCommand(BaseCommand):
    """Displays running logs from the watch."""
    command = 'logs'

    def __call__(self, args):
        super(LogsCommand, self).__call__(args)
        pebble = self._connect(args)
        PebbleLogPrinter(pebble)
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            pass
