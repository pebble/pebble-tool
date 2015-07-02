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

from libpebble2.protocol.logs import AppLogMessage, AppLogShippingControl
from libpebble2.communication.transports.websocket import MessageTargetPhone
from libpebble2.communication.transports.websocket.protocol import WebSocketPhoneAppLog

from pebble_tool.exceptions import PebbleProjectException
from pebble_tool.sdk import get_arm_tools_path
from pebble_tool.sdk.project import PebbleProject

logger = logging.getLogger("pebble_tool.util.logs")


class PebbleLogPrinter(object):
    def __init__(self, pebble):
        """
        :param pebble: libpebble2.communication.PebbleConnection
        """
        self.pebble = pebble
        pebble.send_packet(AppLogShippingControl(enable=True))
        pebble.register_endpoint(AppLogMessage, self.handle_watch_log)
        pebble.register_transport_endpoint(MessageTargetPhone, WebSocketPhoneAppLog, self.handle_phone_log)

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
        print("[{}] {}:{}> {}".format(datetime.now().strftime("%H:%M:%S"), packet.filename,
                                      packet.line_number, packet.message))
        self._maybe_handle_crash(packet.message)

    def handle_phone_log(self, packet):
        assert isinstance(packet, WebSocketPhoneAppLog)
        print("[{}] javascript> {}".format(datetime.now().strftime("%H:%M:%S"),
                                           packet.payload.tostring().decode('utf-8')))

    def _maybe_handle_crash(self, message):
        result = re.search(r"(App|Worker) fault! {([0-9a-f-]{36})} PC: (\S+) LR: (\S+)", message)
        if result is None:
            return
        crash_uuid = uuid.UUID(result.group(2))
        try:
            project = PebbleProject()
        except PebbleProjectException:
            print("Crashed, but no active project available to desym.")
            return
        if crash_uuid != project.uuid:
            print("An app crashed, but it wasn't the active project.")
            return
        self._handle_crash(result.group(1).lower(), result.group(3), result.group(4))

    def _handle_crash(self, process, pc, lr):
        platform = self.pebble.watch_platform
        if platform == 'unknown':
            app_elf_path = "build/pebble-{}.elf".format(process)
        else:
            app_elf_path = "build/{}/pebble-{}.elf".format(platform, process)

        if not os.path.exists(app_elf_path):
            print("Could not look up debugging symbols.")
            print("Could not find ELF file: {}".format(app_elf_path))
            print("Please try rebuilding your project")
            return

        print(self._format_register("Program Counter (PC)", pc, app_elf_path))
        print(self._format_register("Link Register (LR)", lr, app_elf_path))

    def _format_register(self, name, address_str, elf_path):
        try:
            address = int(address_str, 16)
        except ValueError:
            result = '???'
        else:
            if address > 0x20000:
                result = '???'
            else:
                result = subprocess.check_output([os.path.join(get_arm_tools_path(), "arm-none-eabi-addr2line"),
                                                  address_str, "--exe", elf_path]).strip()
        return "{:24}: {:10} {}".format(name, address_str, result)
