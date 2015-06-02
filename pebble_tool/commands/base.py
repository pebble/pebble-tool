__author__ = 'katharine'

import argparse
import os
import threading

from libpebble2.communication import PebbleConnection
from libpebble2.communication.transports.qemu import QemuTransport
from libpebble2.communication.transports.websocket import WebsocketTransport
from libpebble2.events.threaded import ThreadedEventHandler

from pebble_tool.exceptions import ToolError

_CommandRegistry = []


class SelfRegisteringCommand(type):
    def __init__(cls, name, bases, dct):
        if hasattr(cls, 'command') and cls.command is not None:
            _CommandRegistry.append(cls)
        super(SelfRegisteringCommand, cls).__init__(name, bases, dct)


class BaseCommand(object):
    __metaclass__ = SelfRegisteringCommand
    command = None

    @classmethod
    def add_parser(cls, parser):
        parser = parser.add_parser(cls.command, parents=cls._shared_parser())
        parser.set_defaults(func=lambda x: cls()(x))
        return parser

    @classmethod
    def _shared_parser(cls):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--debug', action='store_true', help="Enable debugging output")
        parser.add_argument('--phone', help="When using the developer connection, your phone's IP or hostname.")
        parser.add_argument('--qemu', help="Use this option to connect directly to a QEMU instance.")
        return [parser]

    def __call__(self, args):
        raise NotImplementedError

    def _connect(self, args):
        if args.phone:
            return self._connect_phone(args.phone)
        elif args.qemu:
            return self._connect_qemu(args.qemu)
        else:
            if 'PEBBLE_PHONE' in os.environ:
                return self._connect_phone(os.environ['PEBBLE_PHONE'])
            elif 'PEBBLE_QEMU' in os.environ:
                return self._connect_qemu(os.environ['PEBBLE_QEMU'])
        raise ToolError("No pebble connection specified.")

    def _connect_phone(self, phone):
        parts = phone.split(':')
        ip = parts[0]
        if len(parts) == 2:
            port = int(parts[1])
        else:
            port = 9000
        connection = PebbleConnection(WebsocketTransport("ws://{}:{}/".format(ip, port)), ThreadedEventHandler)
        connection.connect()
        self._pump_connection(connection)
        return connection

    def _connect_qemu(self, qemu):
        parts = qemu.split(':')
        ip = parts[0]
        if not ip:
            ip = '127.0.0.1'
        if len(parts) == 2:
            port = int(parts[1])
        else:
            port = 9000
        connection = PebbleConnection(QemuTransport(ip, port), ThreadedEventHandler)
        connection.connect()
        self._pump_connection(connection)
        return connection

    def _pump_connection(self, connection):
        def pump():
            while True:
                connection.pump_reader()
        thread = threading.Thread(target=pump)
        thread.daemon = True
        thread.start()


def register_children(parser):
    subparsers = parser.add_subparsers()
    for command in _CommandRegistry:
        command.add_parser(subparsers)
