from __future__ import absolute_import
__author__ = 'katharine'

import argparse
from .base import PebbleCommand
from pebble_tool.util.logs import PebbleLogPrinter


class LogsCommand(PebbleCommand):
    """Displays running logs from the watch."""
    command = 'logs'

    def __call__(self, args):
        super(LogsCommand, self).__call__(args)
        force_colour = args.colour if args.colour != args.no_colour else None
        PebbleLogPrinter(self.pebble, force_colour=force_colour).wait()

    @classmethod
    def add_parser(cls, parser):
        parser = super(LogsCommand, cls).add_parser(parser)
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--colour', action='store_true')
        group.add_argument('--no-colour', action='store_true')
        return parser
