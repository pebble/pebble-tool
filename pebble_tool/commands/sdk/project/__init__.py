from __future__ import absolute_import, print_function
__author__ = 'katharine'

import os
import subprocess
import logging

from pebble_tool.exceptions import (PebbleProjectException, InvalidJSONException, InvalidProjectException,
                                    OutdatedProjectException)
from pebble_tool.sdk.project import PebbleProject
from pebble_tool.util.analytics import post_event
from pebble_tool.commands.sdk import SDKCommand

logger = logging.getLogger("pebble_tool.commands.sdk")


class SDKProjectCommand(SDKCommand):
    @property
    def waf_path(self):
        return os.path.join(self.get_sdk_path(), 'pebble', 'waf')

    def _waf(self, command, extra_env=None, args=None):
        if args is None:
            args = []
        else:
            args = list(args)
        if self._verbosity > 0:
            v = '-' + ('v' * self._verbosity)
            args = [v] + args
        virtualenv = os.path.join(self.get_sdk_path(), '..', '.env')
        command = [os.path.join(virtualenv, 'bin', 'python'), self.waf_path, command] + args
        logger.debug("waf command: %s", subprocess.list2cmdline(command))
        env = os.environ.copy()
        env['PYTHONHOME'] = virtualenv
        if os.path.isdir('node_modules'):
            env['PYTHONPATH'] = '' if 'PYTHONPATH' not in env else env['PYTHONPATH'] + ":"
            env['PYTHONPATH'] += ':'.join([os.path.join('node_modules', module) for module in os.listdir('node_modules')])
        if extra_env is not None:
            env.update(extra_env)
        subprocess.check_call(command, env=env)

    def __call__(self, args):
        super(SDKProjectCommand, self).__call__(args)
        try:
            self.project = PebbleProject()
        except PebbleProjectException as e:
            event_map = {
                InvalidProjectException: "sdk_run_without_project",
                InvalidJSONException: "sdk_json_error",
                OutdatedProjectException: "sdk_json_error",
            }
            if type(e) in event_map:
                post_event(event_map[type(e)])
            raise
