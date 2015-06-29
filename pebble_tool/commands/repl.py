from __future__ import absolute_import
__author__ = 'katharine'

import code
import readline
import rlcompleter

import libpebble2.protocol

from .base import BaseCommand


class ReplCommand(BaseCommand):
    command = 'repl'

    def __call__(self, args):
        super(ReplCommand, self).__call__(args)
        pebble = self._connect(args)
        repl_env = {
            'pebble': pebble,
            'protocol': libpebble2.protocol,
        }
        readline.set_completer(rlcompleter.Completer(repl_env).complete)
        readline.parse_and_bind('tab:complete')
        code.interact(local=repl_env)
