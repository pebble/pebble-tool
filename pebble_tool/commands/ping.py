from __future__ import absolute_import, print_function
__author__ = 'katharine'

import random

from libpebble2.protocol.system import PingPong, Ping, Pong

from .base import PebbleCommand


class PingCommand(PebbleCommand):
    """Pings the watch."""
    command = 'ping'

    def __call__(self, args):
        super(PingCommand, self).__call__(args)
        cookie = random.randint(1, 0xFFFFFFFF)
        self.pebble.send_packet(PingPong(cookie=cookie, message=Ping(idle=False)))
        pong = self.pebble.read_from_endpoint(PingPong)
        if pong.cookie == cookie:
            print("Pong!")
        else:
            print("Got wrong cookie: {} (expected {})".format(pong.cookie, cookie))
