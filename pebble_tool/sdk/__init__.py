from __future__ import absolute_import, print_function
__author__ = 'katharine'

import os
import subprocess

from pebble_tool.exceptions import MissingSDK
from pebble_tool.util import get_persist_dir
from .manager import SDKManager

pebble_platforms = ('aplite', 'basalt', 'chalk')

SDK_VERSION = '3'


def sdk_path():
    path = (os.getenv('PEBBLE_SDK_PATH', None) or sdk_manager.current_path)
    if path is None:
        print("No SDK installed; installing the latest one...")
        sdk_manager.install_remote_sdk("latest")
        print("Installed SDK {}.".format(sdk_manager.get_current_sdk()))
        path = sdk_manager.current_path
    if not os.path.exists(os.path.join(path, 'sdk-core', 'pebble', 'waf')):
        raise MissingSDK("SDK unavailable; can't run this command.")
    return path


def sdk_version():
    try:
        from . import version
        return version.version_string
    except ImportError:
        here = os.path.dirname(__file__)
        try:
            return subprocess.check_output(["git", "describe"], cwd=here,
                                           stderr=subprocess.STDOUT).decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            if e.returncode == 128:
                try:
                    return 'g{}'.format(subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=here,
                                                                stderr=subprocess.STDOUT).decode('utf-8')).strip()
                except subprocess.CalledProcessError as e:
                    pass
            return 'unknown'


sdk_manager = SDKManager()

def get_sdk_persist_dir(platform):
    dir = os.path.join(get_persist_dir(), sdk_version(), platform)
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir


def get_arm_tools_path():
    return os.path.join(sdk_path(), "arm-cs-tools", "bin")
