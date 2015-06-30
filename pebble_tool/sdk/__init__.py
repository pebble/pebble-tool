from __future__ import absolute_import
__author__ = 'katharine'

import os
import subprocess

from pebble_tool.exceptions import MissingSDK
from pebble_tool.util import get_persist_dir

pebble_platforms = ('aplite', 'basalt')

SDK_VERSION = '3'


def sdk_path():
    path = os.getenv('PEBBLE_SDK_PATH', None) or os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if not os.path.exists(path):
        raise MissingSDK("SDK unavailable; can't run this command.")
    return path


def sdk_version():
    try:
        from . import version
        return version.version_string
    except ImportError:
        here = os.path.dirname(__file__)
        try:
            return subprocess.check_output(["git", "describe"], cwd=here, stderr=subprocess.STDOUT).strip()
        except subprocess.CalledProcessError as e:
            if e.returncode == 128:
                try:
                    return 'g{}'.format(subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=here,
                                                                stderr=subprocess.STDOUT)).strip()
                except subprocess.CalledProcessError as e:
                    pass
            return 'unknown'


def get_sdk_persist_dir(platform):
    dir = os.path.join(get_persist_dir(), sdk_version(), platform)
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir


def add_arm_tools_to_path(self, args):
    os.environ['PATH'] += ":{}".format(os.path.join(self.sdk_path(args), "arm-cs-tools", "bin"))
