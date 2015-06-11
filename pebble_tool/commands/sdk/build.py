from __future__ import absolute_import, print_function
__author__ = 'katharine'

import os
import subprocess

from pebble_tool.exceptions import ToolError
from pebble_tool.sdk.project import PebbleProject, PebbleProjectException
from . import SDKCommand


class BuildCommand(SDKCommand):
    command = "build"

    def __call__(self, args):
        super(BuildCommand, self).__call__(args)
        try:
            subprocess.check_call([self.waf_path, "configure", "build"])
        except subprocess.CalledProcessError:
            print("Build failed.")


class CleanCommand(SDKCommand):
    command = "clean"

    def __call__(self, args):
        super(CleanCommand, self).__call__(args)
        try:
            subprocess.check_call([self.waf_path, "distclean"])
        except subprocess.CalledProcessError:
            print("Build failed.")
