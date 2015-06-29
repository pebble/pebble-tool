from __future__ import absolute_import
__author__ = 'katharine'

import time

from .base import BaseCommand
from pebble_tool.account import get_default_account


class ReplCommand(BaseCommand):
    command = 'login'

    def __call__(self, args):
        super(ReplCommand, self).__call__(args)
        account = get_default_account()
        account.login(args)

    @classmethod
    def add_parser(cls, parser):
        parser = super(ReplCommand, cls).add_parser(parser)
        parser.add_argument('--auth_host_name', type=str, default='localhost')
        parser.add_argument('--auth_host_port', type=int, nargs='?', default=[60000])
        parser.add_argument('--logging_level', type=str, default='ERROR')
        parser.add_argument('--noauth_local_webserver', action='store_true', default=False,
                            help="Try this flag if the standard authentication isn't working.")
        return parser
