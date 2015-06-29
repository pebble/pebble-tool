from __future__ import absolute_import
__author__ = 'katharine'

import time

from .base import BaseCommand
from pebble_tool.util.logs import PebbleLogPrinter


class ReplCommand(BaseCommand):
    command = 'logs'

    def __call__(self, args):
        super(ReplCommand, self).__call__(args)
        pebble = self._connect(args)
        PebbleLogPrinter(pebble)
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            pass
