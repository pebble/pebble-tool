from __future__ import absolute_import, print_function
__author__ = 'katharine'

from progressbar import ProgressBar, Bar, FileTransferSpeed, Timer, Percentage
import time

from libpebble2.communication.transports.websocket import WebsocketTransport, MessageTargetPhone
from libpebble2.communication.transports.websocket.protocol import WebSocketInstallBundle, WebSocketInstallStatus
from libpebble2.services.install import AppInstaller

from .base import BaseCommand
from ..util.logs import PebbleLogPrinter
from ..exceptions import ToolError


class InstallCommand(BaseCommand):
    command = 'install'

    def __init__(self):
        self.progress_bar = ProgressBar(widgets=[Percentage(), Bar(marker='=', left='[', right=']'), ' ',
                                                 FileTransferSpeed(), ' ', Timer(format='%s')])

    def __call__(self, args):
        super(InstallCommand, self).__call__(args)
        pebble = self._connect(args)
        if isinstance(pebble.transport, WebsocketTransport):
            self._install_via_websocket(pebble, args.pbw)
        else:
            self._install_via_serial(pebble, args.pbw)
        if args.logs:
            PebbleLogPrinter(pebble)
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                pass

    def _install_via_serial(self, pebble, pbw):
        installer = AppInstaller(pebble, pbw)
        self.progress_bar.maxval = installer.total_size
        self.progress_bar.start()
        installer.register_handler("progress", self._handle_pp_progress)
        installer.install()
        self.progress_bar.finish()

    def _handle_pp_progress(self, sent, total_sent, total_size):
        self.progress_bar.update(total_sent)

    def _install_via_websocket(self, pebble, pbw):
        with open(pbw) as f:
            print("Installing app...")
            pebble.transport.send_packet(WebSocketInstallBundle(pbw=f.read()), target=MessageTargetPhone())
            result = pebble.read_transport_message(MessageTargetPhone, WebSocketInstallStatus)
            if result.status != WebSocketInstallStatus.StatusCode.Success:
                raise ToolError("App install failed.")
            else:
                print("App install succeeded.")

    @classmethod
    def add_parser(cls, parser):
        parser = super(InstallCommand, cls).add_parser(parser)
        parser.add_argument('pbw', help="Path to app to install.")
        parser.add_argument('--logs', action="store_true", help="Enable logs")
        return parser
