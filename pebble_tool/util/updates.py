from __future__ import absolute_import, print_function
__author__ = 'katharine'

import atexit
import logging
import os
import requests
import threading
import time

from pebble_tool.version import __version__
from pebble_tool.sdk import sdk_manager

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
        latest = requests.get("https://sdk.getpebble.com/v1/files/{}/latest".format(self.component))
        if not 200 <= latest.status_code < 400:
            logger.info("Update check failed: %s (%s)", latest.status_code, latest.reason)
            atexit.register(self.callback, 'v4.0-rc1')
            return

        result = latest.json()
        if result['version'] != self.current_version:
            logger.debug("Found an update: %s", result['version'])
            atexit.register(self.callback, result['version'])


def _handle_sdk_update(version):
    if not version in sdk_manager.list_local_sdk_versions():
        print("A new SDK, version {0}, is available! Run `pebble sdk install {0}` to get it.".format(version))


def _handle_tool_update(version):
    print("An updated pebble tool, version {}, is available.".format(version))
    if 'PEBBLE_IS_HOMEBREW' in os.environ:
        if 'rc' in version or 'beta' in version or 'dp' in version:
            devel = " --devel"
        else:
            devel = ""
        print("Run `brew update && brew upgrade{} pebble-sdk` to get it.".format(devel))
    else:
        print("Head to https://developer.getpebble.com/sdk/ to get it.")


def wait_for_update_checks(timeout):
    now = time.time()
    end = now + timeout
    for checker in _checkers:
        now = time.time()
        if now > end:
            break
        checker.join(end - time.time())

_checkers = [UpdateChecker("pebble-tool", __version__, _handle_tool_update)]

# Only do the SDK update check if there is actually an SDK installed.
if sdk_manager.get_current_sdk() is not None:
    _checkers.append(UpdateChecker("sdk-core", "", _handle_sdk_update))
