from __future__ import absolute_import, print_function
__author__ = 'katharine'

import os
import subprocess

from pebble_tool.exceptions import (ToolError, MissingSDK, PebbleProjectException, InvalidJSONException,
                                    InvalidProjectException, OutdatedProjectException)
from pebble_tool.sdk import get_arm_tools_path, sdk_path
from pebble_tool.sdk.project import PebbleProject
from pebble_tool.util.analytics import post_event
from ..base import BaseCommand


class SDKCommand(BaseCommand):
    def get_sdk_path(self):
        path = sdk_path()
        if not os.path.exists(os.path.join(path, 'Pebble', 'waf')):
            raise MissingSDK("SDK unavailable; can't run this command.")
        return path

    @property
    def waf_path(self):
        return os.path.join(self.get_sdk_path(), 'Pebble', 'waf')

    def add_arm_tools_to_path(self):
        os.environ['PATH'] += ":{}".format(get_arm_tools_path())

    def _fix_python(self):
        # First figure out what 'python' means:
        try:
            version = int(subprocess.check_output(["python", "-c", "import sys; print sys.version_info[0]"]).strip())
        except (subprocess.CalledProcessError, ValueError):
            raise ToolError("'python' doesn't mean anything on this system.")

        if version != 2:
            try:
                python2_version = int(subprocess.check_output(["python2", "-c",
                                                                "import sys; print sys.version_info[1]"]).strip())
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
        subprocess.check_call([self.waf_path, command] + args)

    def __call__(self, args):
        super(SDKCommand, self).__call__(args)
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
        self.add_arm_tools_to_path()
