from __future__ import absolute_import, print_function
__author__ = 'katharine'

from datetime import datetime

from libpebble2.protocol.logs import AppLogMessage, AppLogShippingControl
from libpebble2.communication.transports.websocket import MessageTargetPhone
from libpebble2.communication.transports.websocket.protocol import WebSocketPhoneAppLog


class PebbleLogPrinter(object):
    def __init__(self, pebble):
        """
        :param pebble: libpebble2.communication.PebbleConnection
        """
        pebble.send_packet(AppLogShippingControl(enable=True))
        pebble.register_endpoint(AppLogMessage, self.handle_watch_log)
        pebble.register_transport_endpoint(MessageTargetPhone, WebSocketPhoneAppLog, self.handle_phone_log)

    def handle_watch_log(self, packet):
        assert isinstance(packet, AppLogMessage)
        # We do actually know the original timestamp of the log (it's in packet.timestamp), but if we
        # use it that it meshes oddly with the JS logs, which must use the user's system time.
        print("[{}] {}:{}> {}".format(datetime.now().strftime("%H:%M:%S"), packet.filename,
                                      packet.line_number, packet.message))

    def handle_phone_log(self, packet):
        assert isinstance(packet, WebSocketPhoneAppLog)
        print("[{}] javascript> {}".format(datetime.now().strftime("%H:%M:%S"),
                                           packet.payload.tostring().decode('utf-8')))
