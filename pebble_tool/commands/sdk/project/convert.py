from __future__ import absolute_import, print_function

import collections
import hashlib
import json
import os

from shutil import copy2

from pebble_tool.commands.sdk.project import SDKProjectCommand
from pebble_tool.sdk.project import PebbleProject, OutdatedProjectException
from pebble_tool.sdk import pebble_platforms


class PblProjectConverter(SDKProjectCommand):
    """Structurally converts an SDK 2 project to an SDK 3 project. Code changes may still be required."""
    command = 'convert-project'

    def __call__(self, args):
        try:
            super(PblProjectConverter, self).__call__(args)
            print("No conversion required")
        except OutdatedProjectException:
            self._convert_project()
            print("Project successfully converted!")

    def _convert_project(self):
        project_root = os.getcwd()
        project_template_path = os.path.join(self.get_sdk_path(), 'pebble', 'common', 'templates')

        self._generate_appinfo_from_old_project(project_root)

        wscript_path = os.path.join(project_root, "wscript")

        wscript2_hash = hashlib.md5(open(os.path.join(project_template_path, 'wscript_sdk2')).read()).hexdigest()
        wscript3_hash = hashlib.md5(open(os.path.join(project_template_path, 'wscript')).read()).hexdigest()
        with open(wscript_path, "r") as f:
            current_hash = hashlib.md5(f.read()).hexdigest()

        if wscript2_hash != current_hash and wscript3_hash != current_hash:
            print('WARNING: You had modified your wscript and those changes will be lost.\n'
                  'Saving your old wscript in wscript.backup.')
            os.rename(wscript_path, wscript_path + '.backup')

        print('Generating new 3.x wscript')
        copy2(os.path.join(project_template_path, 'wscript'), wscript_path)
        os.system('pebble clean')

    @classmethod
    def _generate_appinfo_from_old_project(cls, project_root):
        app_info_path = os.path.join(project_root, "appinfo.json")
        with open(app_info_path, "r") as f:
            app_info_json = json.load(f, object_pairs_hook=collections.OrderedDict)

        app_info_json["targetPlatforms"] = pebble_platforms
        app_info_json["sdkVersion"] = "3"

        with open(app_info_path, "w") as f:
            json.dump(app_info_json, f, indent=2, separators=(',', ': '))
