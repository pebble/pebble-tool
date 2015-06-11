__author__ = 'katharine'

import os

from pebble_tool.exceptions import MissingSDK


def sdk_path():
    path = os.getenv('PEBBLE_SDK_PATH', None) or os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if not os.path.exists(path):
        raise MissingSDK("SDK unavailable; can't run this command.")
    return path


def add_arm_tools_to_path(self, args):
    os.environ['PATH'] += ":{}".format(os.path.join(self.sdk_path(args), "arm-cs-tools", "bin"))