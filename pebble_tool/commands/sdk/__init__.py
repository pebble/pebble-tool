from __future__ import absolute_import, print_function
__author__ = 'katharine'

import os
import subprocess
import logging

from pebble_tool.exceptions import (ToolError, MissingSDK, PebbleProjectException, InvalidJSONException,
                                    InvalidProjectException, OutdatedProjectException)
from pebble_tool.sdk import add_tools_to_path, sdk_path, sdk_manager
from pebble_tool.sdk.project import PebbleProject
from pebble_tool.util.analytics import post_event
from ..base import BaseCommand

logger = logging.getLogger("pebble_tool.commands.sdk")


class SDKCommand(BaseCommand):
    def get_sdk_path(self):
        path = sdk_manager.path_for_sdk(self.sdk) if self.sdk is not None else sdk_path()
        logger.debug("SDK path: %s", path)
        if not os.path.exists(os.path.join(path, 'pebble', 'waf')):
            raise MissingSDK("SDK unavailable; can't run this command.")
        return path

    @property
    def waf_path(self):
        return os.path.join(self.get_sdk_path(), 'pebble', 'waf')

    @classmethod
    def add_parser(cls, parser):
        parser = super(SDKCommand, cls).add_parser(parser)
        parser.add_argument('--sdk', nargs='?', help='SDK version to use for this command, if not the '
                                                     'currently selected one.')
        return parser

    def add_arm_tools_to_path(self):
        add_tools_to_path()

    def _fix_python(self):
        # First figure out what 'python' means:
        try:
            version = int(subprocess.check_output(["python", "-c", "import sys; print(sys.version_info[0])"]).strip())
        except (subprocess.CalledProcessError, ValueError):
            raise ToolError("'python' doesn't mean anything on this system.")

        if version != 2:
            try:
                python2_version = int(subprocess.check_output(["python2", "-c",
                                                                "import sys; print(sys.version_info[1])"]).strip())
            except (subprocess.CalledProcessError, ValueError):
                raise ToolError("Can't find a python2 interpreter.")
            if python2_version < 6:
                raise ToolError("Require python 2.6 or 2.7 to run the build tools; got 2.{}".format(python2_version))
            # We have a viable python2. Use our hack to stick 'python' into the path.
            os.environ['PATH'] = '{}:{}'.format(os.path.normpath(os.path.dirname(__file__)), os.environ['PATH'])

    def _waf(self, command, *args):
        args = list(args)
        if self._verbosity > 0:
            v = '-' + ('v' * self._verbosity)
            args = [v] + args
        virtualenv = os.path.join(self.get_sdk_path(), '..', '.env')
        command = [os.path.join(virtualenv, 'bin', 'python'), self.waf_path, command] + args
        logger.debug("waf command: %s", subprocess.list2cmdline(command))

        new_env = os.environ.copy()
        new_env['PYTHONHOME'] = virtualenv

        subprocess.check_call(command, env=new_env)

    def __call__(self, args):
        super(SDKCommand, self).__call__(args)
        self.sdk = args.sdk
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
        self._fix_python()
        self.add_arm_tools_to_path()
