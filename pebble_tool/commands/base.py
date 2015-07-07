__author__ = 'katharine'

from six import with_metaclass

import argparse
import logging
import os
import time

from libpebble2.communication import PebbleConnection
from libpebble2.communication.transports.qemu import QemuTransport
from libpebble2.communication.transports.websocket import WebsocketTransport
from libpebble2.exceptions import ConnectionError
from libpebble2.protocol.system import TimeMessage, SetUTC

from pebble_tool.exceptions import ToolError
from pebble_tool.sdk import pebble_platforms
from pebble_tool.sdk.emulator import ManagedEmulatorTransport
from pebble_tool.sdk.cloudpebble import CloudPebbleTransport
from pebble_tool.util.analytics import post_event

_CommandRegistry = []


class SelfRegisteringCommand(type):
    def __init__(cls, name, bases, dct):
        if hasattr(cls, 'command') and cls.command is not None:
            _CommandRegistry.append(cls)
        super(SelfRegisteringCommand, cls).__init__(name, bases, dct)


class BaseCommand(with_metaclass(SelfRegisteringCommand)):
    command = None

    @classmethod
    def add_parser(cls, parser):
        parser = parser.add_parser(cls.command, parents=cls._shared_parser(), help=cls.__doc__)
        parser.set_defaults(func=lambda x: cls()(x))
        return parser

    @classmethod
    def _shared_parser(cls):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('-v', action='count', default=0, help="Degree of verbosity (use more v for more verbosity)")
        return [parser]

    def __call__(self, args):
        self._extra_args = args.waf
        self._set_debugging(args.v)
        post_event("invoke_command_{}".format(self.command))

    def _set_debugging(self, level):
        self._verbosity = level
        if level is not None:
            if level == 1:
                verbosity = logging.INFO
            elif level >= 2:
                verbosity = logging.DEBUG
            else:
                verbosity = logging.WARNING
            logging.getLogger().setLevel(verbosity)


class PebbleCommand(BaseCommand):
    @classmethod
    def _shared_parser(cls):
        parser = argparse.ArgumentParser(add_help=False)
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--phone', metavar='phone_ip',
                            help="When using the developer connection, your phone's IP or hostname. "
                                 "Equivalent to PEBBLE_PHONE.")
        group.add_argument('--qemu', nargs='?', const='localhost:12344', metavar='host',
                            help="Use this option to connect directly to a QEMU instance. Equivalent to PEBBLE_QEMU.")
        group.add_argument('--cloudpebble', action='store_true', help="Use this option to connect to your phone via "
                                                                       "the CloudPebble connection. Equivalent to "
                                                                       "PEBBLE_CLOUDPEBBLE.")
        group.add_argument('--emulator', type=str, help="Launch an emulator. Equivalent to PEBBLE_EMULATOR.",
                           choices=pebble_platforms)
        return super(PebbleCommand, cls)._shared_parser() + [parser]

    def __call__(self, args):
        super(PebbleCommand, self).__call__(args)
        try:
            self.pebble = self._connect(args)
        except ConnectionError as e:
            raise ToolError(str(e))

    def _connect(self, args):
        self._set_debugging(args.v)
        if args.phone:
            return self._connect_phone(args.phone)
        elif args.qemu:
            return self._connect_qemu(args.qemu)
        elif args.emulator:
            return self._connect_emulator(args.emulator)
        elif args.cloudpebble:
            return self._connect_cloudpebble()
        else:
            if 'PEBBLE_PHONE' in os.environ:
                return self._connect_phone(os.environ['PEBBLE_PHONE'])
            elif 'PEBBLE_QEMU' in os.environ:
                return self._connect_qemu(os.environ['PEBBLE_QEMU'])
            elif 'PEBBLE_EMULATOR' in os.environ:
                platform = os.environ['PEBBLE_EMULATOR']
                if platform not in pebble_platforms:
                    raise ToolError("PEBBLE_EMULATOR is set to '{}', which is not a valid platform "
                                    "(pick from {})".format(platform, ', '.join(pebble_platforms)))
                return self._connect_emulator(platform)
            elif os.environ.get('PEBBLE_EMULATOR', False):
                return self._connect_cloudpebble()
        raise ToolError("No pebble connection specified.")

    def _connect_phone(self, phone):
        parts = phone.split(':')
        ip = parts[0]
        if len(parts) == 2:
            port = int(parts[1])
        else:
            port = 9000
        connection = PebbleConnection(WebsocketTransport("ws://{}:{}/".format(ip, port)), **self._get_debug_args())
        connection.connect()
        connection.run_async()
        return connection

    def _connect_qemu(self, qemu):
        parts = qemu.split(':')
        ip = parts[0]
        if not ip:
            ip = '127.0.0.1'
        if len(parts) == 2:
            port = int(parts[1])
        else:
            port = 12344
        connection = PebbleConnection(QemuTransport(ip, port), **self._get_debug_args())
        connection.connect()
        connection.run_async()
        return connection

    def _connect_emulator(self, platform):
        connection = PebbleConnection(ManagedEmulatorTransport(platform), **self._get_debug_args())
        connection.connect()
        connection.run_async()
        # Make sure the timezone is set usefully.
        if platform != "aplite":
            ts = time.time()
            tz_offset = -time.altzone if time.localtime(ts).tm_isdst and time.daylight else -time.altzone
            tz_offset_minutes = tz_offset // 60
            tz_name = "UTC%+d" % (tz_offset_minutes / 60)
            connection.send_packet(TimeMessage(message=SetUTC(unix_time=ts, utc_offset=tz_offset_minutes, tz_name=tz_name)))
        return connection

    def _connect_cloudpebble(self):
        connection = PebbleConnection(CloudPebbleTransport(), **self._get_debug_args())
        connection.connect()
        connection.run_async()
        return connection

    def _get_debug_args(self):
        args = {}
        if self._verbosity >= 3:
            args['log_packet_level'] = logging.DEBUG
        if self._verbosity >= 4:
            args['log_protocol_level'] = logging.DEBUG
        return args


def register_children(parser):
    subparsers = parser.add_subparsers(title="Command")
    for command in _CommandRegistry:
        command.add_parser(subparsers)
