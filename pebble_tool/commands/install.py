from __future__ import absolute_import, print_function
__author__ = 'katharine'

import os
import os.path
from progressbar import ProgressBar, Bar, FileTransferSpeed, Timer, Percentage

from libpebble2.communication.transports.websocket import WebsocketTransport, MessageTargetPhone
from libpebble2.communication.transports.websocket.protocol import WebSocketInstallBundle, WebSocketInstallStatus
from libpebble2.exceptions import TimeoutError
from libpebble2.services.install import AppInstaller

from .base import PebbleCommand
from ..util.logs import PebbleLogPrinter
from ..exceptions import ToolError


class InstallCommand(PebbleCommand):
    """Installs the given app on the watch."""
    command = 'install'

    def __init__(self):
        self.progress_bar = ProgressBar(widgets=[Percentage(), Bar(marker='=', left='[', right=']'), ' ',
                                                 FileTransferSpeed(), ' ', Timer(format='%s')])

    def __call__(self, args):
        super(InstallCommand, self).__call__(args)
        pbw = args.pbw or 'build/{}.pbw'.format(os.path.basename(os.getcwd()))
        try:
            if isinstance(self.pebble.transport, WebsocketTransport):
                self._install_via_websocket(self.pebble, pbw)
            else:
                self._install_via_serial(self.pebble, pbw)
        except IOError as e:
            if args.pbw is None:
                raise ToolError("You must either run this command from a project directory or specify the pbw "
                                "to install.")
            else:
                raise ToolError(str(e))
        if args.logs:
            PebbleLogPrinter(self.pebble).wait()

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
            try:
                result = pebble.read_transport_message(MessageTargetPhone, WebSocketInstallStatus, timeout=300)
            except TimeoutError:
                raise ToolError("Timed out waiting for install confirmation.")
            if result.status != WebSocketInstallStatus.StatusCode.Success:
                raise ToolError("App install failed.")
            else:
                print("App install succeeded.")

    @classmethod
    def add_parser(cls, parser):
        parser = super(InstallCommand, cls).add_parser(parser)
        parser.add_argument('pbw', help="Path to app to install.", nargs='?', default=None)
        parser.add_argument('--logs', action="store_true", help="Enable logs")
        return parser
