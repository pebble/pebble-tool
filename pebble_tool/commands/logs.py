from __future__ import absolute_import
__author__ = 'katharine'

import time

from .base import PebbleCommand
from pebble_tool.util.logs import PebbleLogPrinter


class LogsCommand(PebbleCommand):
    """Displays running logs from the watch."""
    command = 'logs'

    def __call__(self, args):
        super(LogsCommand, self).__call__(args)
        PebbleLogPrinter(self.pebble)
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            pass
