from __future__ import absolute_import
__author__ = 'cherie'

from .base import PebbleCommand


class EmuAccelCommand(PebbleCommand):
    command = 'emu-accel'

    def __call__(self, args):
        super(EmuAccelCommand, self).__call__(args)
        print "Running {}".format(self.command)

    @classmethod
    def add_parser(cls, parser):
        parser = super(EmuAccelCommand, cls).add_parser(parser)
        parser.add_argument('motion',
                            choices=['tilt-left', 'tilt-right', 'tilt-forward', 'tilt-back', 'gravity+x',
                                     'gravity-x', 'gravity+y', 'gravity-y', 'gravity+z', 'gravity-z',
                                     'custom'],
                            default=None,
                            help="The type of accelerometer motion to send to the emulator. If using an accel file, "
                                 "specify 'custom' and then specify the filename using the '--file' option")
        parser.add_argument('--file', help="Filename of the file containing custom accel data. Each line of this text "
                                           "file should contain the comma-separated x, y, and z readings. (e.g. "
                                           "'-24, -88, -1032')")
        return parser


class EmuAppConfigCommand(PebbleCommand):
    command = 'emu-app-config'

    def __call__(self, args):
        super(EmuAppConfigCommand, self).__call__(args)
        print "Running {}".format(self.command)


class EmuBatteryCommand(PebbleCommand):
    command = 'emu-battery'

    def __call__(self, args):
        super(EmuBatteryCommand, self).__call__(args)
        print "Running {}".format(self.command)

    @classmethod
    def add_parser(cls, parser):
        parser = super(EmuBatteryCommand, cls).add_parser(parser)
        parser.add_argument('--pct', default=80, help="Set the percentage battery remaining (0 to 100) on the emulator")
        parser.add_argument('--charging', action='store_true', help="Set the Pebble emulator to charging mode")
        return parser


class EmuButtonCommand(PebbleCommand):
    command = 'emu-button'

    def __call__(self, args):
        super(EmuButtonCommand, self).__call__(args)
        print "Running {}".format(self.command)

    @classmethod
    def add_parser(cls, parser):
        parser = super(EmuButtonCommand, cls).add_parser(parser)
        parser.add_argument('button', choices=['back', 'up', 'select', 'down'], default=None,
                            help="Send a button press to the emulator")
        return parser


class EmuBluetoothConnectionCommand(PebbleCommand):
    command = 'emu-bt-connection'

    def __call__(self, args):
        super(EmuBluetoothConnectionCommand, self).__call__(args)
        print "Running {}".format(self.command)

    @classmethod
    def add_parser(cls, parser):
        parser = super(EmuBluetoothConnectionCommand, cls).add_parser(parser)
        parser.add_argument('--connected', choices=['no', 'yes'], default='yes',
                            help="Set the emulator BT connection status")
        return parser


class EmuCompassCommand(PebbleCommand):
    command = 'emu-compass'

    def __call__(self, args):
        super(EmuCompassCommand, self).__call__(args)
        print "Running {}".format(self.command)

    @classmethod
    def add_parser(cls, parser):
        parser = super(EmuCompassCommand, cls).add_parser(parser)
        parser.add_argument('--heading', default=0, help="Set the emulator compass heading (0 to 359)")
        parser.add_argument('--calib', choices=['invalid', 'calibrating', 'calibrated'], default='calibrated',
                            help="Set the emulator compass calibration status")
        return parser


class EmuTapCommand(PebbleCommand):
    command = 'emu-tap'

    def __call__(self, args):
        super(EmuTapCommand, self).__call__(args)
        print "Running {}".format(self.command)
        # try:
        #     if isinstance(self.pebble.transport, ManagedEmulatorTransport):
        #         packet = QemuPacket(data=QemuTap.Axis.Y, direction=-1)
        #         serialised = packet.serialise()
        #         self.pebble.transport.send_packet(WebSocketRelayQemu(protocol=packet.protocol, data=serialised),
        #                                           target=MessageTargetPhone())
        #     elif isinstance(self.pebble.transport, QemuTransport):
        #         self.pebble.transport.send_packet(QemuTap(axis=QemuTap.Axis.X, direction=1),
        #                                           target=MessageTargetQemu())
        # except Exception as e:
        #     print e

    @classmethod
    def add_parser(cls, parser):
        parser = super(EmuTapCommand, cls).add_parser(parser)
        parser.add_argument('--direction', choices=['+x', '-x', '+y', '-y', '+z', '-z'], default='+x',
                            help="Set the direction of the accel tap in the emulator")
        return parser
