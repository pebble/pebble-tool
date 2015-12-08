from __future__ import absolute_import, print_function
__author__ = 'katharine'

import atexit
import logging
import math
import os
import requests
import sys
import threading
import time

from pebble_tool.version import __version__
from pebble_tool.sdk import sdk_manager
from pebble_tool.util.config import config

logger = logging.getLogger("pebble_tool.util.updates")


class UpdateChecker(threading.Thread):
    def __init__(self, component, current_version, callback):
        self.component = component
        self.current_version = current_version
        self.callback = callback
        super(UpdateChecker, self).__init__()
        self.daemon = True
        self.start()

    def run(self):
        last_check = config.get('update-checks', {}).get(self.component, {})
        if last_check.get('timestamp', 0) < time.time() - 86400:  # minus one day
            logger.debug("Haven't looked for updates lately; checking...")
            latest = sdk_manager.request("/v1/files/{}/latest?channel={}"
                                  .format(self.component, sdk_manager.get_channel()))
            if not 200 <= latest.status_code < 400:
                logger.info("Update check failed: %s (%s)", latest.status_code, latest.reason)
                return

            result = latest.json()
            with config.lock:
                config.setdefault('update-checks', {})[self.component] = {
                    'timestamp': time.time(),
                    'version': result['version'],
                }
            self._check_version(result['version'])
        else:
            self._check_version(last_check['version'])

    def _check_version(self, new_version):
        if new_version != self.current_version:
            logger.debug("Found an update: %s", new_version)
            atexit.register(self.callback, new_version)


def _handle_sdk_update(version):
    if not version in sdk_manager.list_local_sdk_versions():
        print()
        print("A new SDK, version {0}, is available! Run `pebble sdk install {0}` to get it.".format(version))


def _handle_tool_update(version):
    print()
    print("An updated pebble tool, version {}, is available.".format(version))
    if 'PEBBLE_IS_HOMEBREW' in os.environ:
        print("Run `brew update && brew upgrade pebble-sdk` to get it.")
    else:
        print("Head to https://developer.getpebble.com/sdk/beta/ to get it.")


def _get_platform():
    sys_platform = sys.platform.rstrip('2')  # "linux2" on python < 3.3...
    return sys_platform + str(int(round(math.log(sys.maxint, 2)+1)))


def wait_for_update_checks(timeout):
    now = time.time()
    end = now + timeout
    for checker in _checkers:
        now = time.time()
        if now > end:
            break
        checker.join(end - time.time())

_checkers = []


def _do_updates():
    _checkers.append(UpdateChecker("pebble-tool-{}".format(_get_platform()), __version__, _handle_tool_update))
    # Only do the SDK update check if there is actually an SDK installed.
    if sdk_manager.get_current_sdk() is not None:
        _checkers.append(UpdateChecker("sdk-core", "", _handle_sdk_update))

_do_updates()
