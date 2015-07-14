from __future__ import absolute_import, print_function
__author__ = 'katharine'

from datetime import datetime
import logging
import os
import os.path
import re
import subprocess
import time
import uuid
import sys

from functools import partial
from collections import OrderedDict
from libpebble2.protocol.logs import AppLogMessage, AppLogShippingControl
from libpebble2.communication.transports.websocket import MessageTargetPhone
from libpebble2.communication.transports.websocket.protocol import WebSocketPhoneAppLog

from pebble_tool.exceptions import PebbleProjectException, MissingSDK
from pebble_tool.sdk import get_arm_tools_path
from pebble_tool.sdk.project import PebbleProject
import colors

logger = logging.getLogger("pebble_tool.util.logs")


class PebbleLogPrinter(object):
    colour_scheme = OrderedDict([
        # LOG_LEVEL_DEBUG_VERBOSE
        (255, colors.cyan),
        # LOG_LEVEL_DEBUG
        (200, colors.magenta),
        # LOG_LEVEL_INFO
        (100, None),
        # LOG_LEVEL_WARNING
        (50, colors.red),
        # LOG_LEVEL_ERROR
        (1, partial(colors.color, fg='white', bg='red')),
        # LOG_LEVEL_ALWAYS
        (0, None)])
    phone_colour = None

    def __init__(self, pebble, force_colour=None):
        """
        :param pebble: libpebble2.communication.PebbleConnection
        :param force_colour: Bool
        """
        self.test_colours = list(self.colour_scheme)
        self.pebble = pebble
        self.print_with_colour = force_colour if force_colour is not None else sys.stdout.isatty()
        pebble.send_packet(AppLogShippingControl(enable=True))
        pebble.register_endpoint(AppLogMessage, self.handle_watch_log)
        pebble.register_transport_endpoint(MessageTargetPhone, WebSocketPhoneAppLog, self.handle_phone_log)
        try:
            os.environ['PATH'] += ":{}".format(get_arm_tools_path())
        except MissingSDK:
            pass

    def _print(self, packet, message):
        colour = self._get_colour(packet)
        if colour:
            print(colour(message))
        else:
            print(message)

    def _get_colour(self, packet):
        colour = None
        if self.print_with_colour:
            if isinstance(packet, WebSocketPhoneAppLog):
                colour = self.phone_colour
            else:
                try:
                    colour = self.colour_scheme[packet.level]
                except KeyError:
                    # Select the next lowest level if the exact level is not in the color scheme
                    colour = next(self.colour_scheme[level] for level in self.colour_scheme if packet.level >= level)
        if len(self.test_colours) > 0:
            colour = self.colour_scheme[self.test_colours.pop()]
        return colour

    def wait(self):
        try:
            while self.pebble.connected:
                time.sleep(1)
        except KeyboardInterrupt:
            return
        else:
            print("Disconnected.")

    def handle_watch_log(self, packet):
        assert isinstance(packet, AppLogMessage)

        # We do actually know the original timestamp of the log (it's in packet.timestamp), but if we
        # use it that it meshes oddly with the JS logs, which must use the user's system time.
        self._print(packet, "[{}] {}:{}> {}".format(datetime.now().strftime("%H:%M:%S"), packet.filename,
                                                    packet.line_number, packet.message))
        self._maybe_handle_crash(packet)

    def handle_phone_log(self, packet):
        assert isinstance(packet, WebSocketPhoneAppLog)
        self._print(packet, "[{}] javascript> {}".format(datetime.now().strftime("%H:%M:%S"),
                                                         packet.payload.decode('utf-8')))

    def _maybe_handle_crash(self, packet):
        result = re.search(r"(App|Worker) fault! {([0-9a-f-]{36})} PC: (\S+) LR: (\S+)", packet.message)
        if result is None:
            return
        crash_uuid = uuid.UUID(result.group(2))
        try:
            project = PebbleProject()
        except PebbleProjectException:
            self._print(packet, "Crashed, but no active project available to desym.")
            return
        if crash_uuid != project.uuid:
            self._print(packet, "An app crashed, but it wasn't the active project.")
            return
        self._handle_crash(packet, result.group(1).lower(), result.group(3), result.group(4))

    def _handle_crash(self, packet, process, pc, lr):

        platform = self.pebble.watch_platform
        if platform == 'unknown':
            app_elf_path = "build/pebble-{}.elf".format(process)
        else:
            app_elf_path = "build/{}/pebble-{}.elf".format(platform, process)

        if not os.path.exists(app_elf_path):
            self._print(packet, "Could not look up debugging symbols.")
            self._print(packet, "Could not find ELF file: {}".format(app_elf_path))
            self._print(packet, "Please try rebuilding your project")
            return

        self._print(packet, self._format_register("Program Counter (PC)", pc, app_elf_path))
        self._print(packet, self._format_register("Link Register (LR)", lr, app_elf_path))

    def _format_register(self, name, address_str, elf_path):
        try:
            address = int(address_str, 16)
        except ValueError:
            result = '???'
        else:
            if address > 0x20000:
                result = '???'
            else:
                try:
                    result = subprocess.check_output(["arm-none-eabi-addr2line", address_str, "--exe",
                                                      elf_path]).strip()
                except OSError:
                    return "(lookup failed: toolchain not found)"
                except subprocess.CalledProcessError:
                    return "???"
        return "{:24}: {:10} {}".format(name, address_str, result)
