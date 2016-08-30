from __future__ import absolute_import, print_function

import collections
import json
import os

from copy import deepcopy
from shutil import copy2, copytree, ignore_patterns, move, rmtree

from pebble_tool.commands.sdk.project import SDKProjectCommand
from pebble_tool.exceptions import OutdatedProjectException, ToolError
from pebble_tool.sdk.project import NpmProject
from pebble_tool.sdk import pebble_platforms


class PblProjectConverter(SDKProjectCommand):
    """Converts an appinfo project from SDK 2 or SDK 3 to a modern package.json project."""
    command = 'convert-project'

    def __call__(self, args):
        try:
            super(PblProjectConverter, self).__call__(args)
            if not isinstance(self.project, NpmProject):
                self._convert_to_npm()
                print("Converted to package.json format.")
            else:
                print("No conversion required")
        except OutdatedProjectException:
            self._generate_appinfo_from_old_project(os.getcwd())
            super(PblProjectConverter, self).__call__(args)
            self._convert_project(move_files=args.move)
            self._convert_to_npm()
            print("Project successfully converted!")

    def _convert_to_npm(self):
        new_info = {
            'name': self.project.short_name,
            'author': self.project.company_name,
            'version': self.project.version + '.0',
            'private': True,
            'keywords': ['pebble-app'],
            'dependencies': {},
            'pebble': {
                'sdkVersion': self.project.sdk_version,
                'targetPlatforms': self.project.target_platforms,
                'enableMultiJS': self.project.enable_multi_js,
                'capabilities': self.project.capabilities,
                'projectType': self.project.project_type,
                'displayName': self.project.long_name,
                'uuid': str(self.project.uuid),
                'watchapp': {
                    'watchface': self.project.is_watchface,
                    'hiddenApp': self.project.is_hidden,
                    'onlyShownOnCommunication': self.project.is_shown_only_on_communication,
                },
                'resources': self.project.resources,
                'messageKeys': self.project.message_keys,
            }
        }
        if os.path.exists('package.json'):
            with open('package.json') as f:
                try:
                    new_info.update(json.load(f))
                except ValueError:
                    raise ToolError("An invalid package.json already exists; conversion aborted.")
            copy2('package.json', 'package.json~')
            print("A package.json already exists. It has been backed up to package.json~.")
        with open('package.json', 'w') as f:
            json.dump(new_info, f, indent=2, separators=(',', ': '))
        os.unlink('appinfo.json')

        self._ignore_npm()

    def _ignore_npm(self):
        if os.path.exists('.gitignore'):
            with open('.gitignore') as f:
                content = f.read()
                if 'node_modules' in content:
                    return

            with open('.gitignore', 'a') as f:
                f.write("\nnode_modules/\n")

    def _convert_project(self, move_files=False):
        # Map project type naming between projectType and sdk-core's types
        option_mapping = {
            "native": "app",
            "package": "lib",
            "rocky": "rocky"
        }
        option = option_mapping[self.project.project_type]

        project_template_path = os.path.join(self.get_sdk_path(), 'pebble', 'common', 'templates')
        if not os.path.exists(project_template_path):
            project_template_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'sdk', 'templates')

        # Read in conversion mapping JSON file, use fallback of app wscript-update only if none
        conversion_specification = os.path.join(project_template_path, 'convert.json')
        conversion_map = {
            "app": {
                "update": ["wscript"]
            }
        }
        if os.path.exists(conversion_specification):
            with open(conversion_specification) as f:
                conversion_map = json.load(f)

        # Read in template mapping JSON file, use fallback of template folder if none
        template_specification = os.path.join(project_template_path, 'templates.json')
        if os.path.exists(template_specification):
            with open(template_specification) as f:
                template_map = json.load(f)

        if "update" in conversion_map[option]:
            for update_file in conversion_map[option]["update"]:
                file_path = os.path.join(os.getcwd(), update_file)
                backup_file = file_path + '.backup'
                if os.path.exists(file_path):
                    os.rename(file_path, backup_file)
                    print("A '{file}' already exists. Backup of {file} saved to {backup}".
                          format(file=update_file, backup=backup_file))

                try:
                    copy2(template_map["default"][update_file], file_path)
                except KeyError:
                    try:
                        template = template_map[option]["default"][update_file]
                        copy2(os.path.join(project_template_path, template), file_path)
                    except KeyError:
                        raise ToolError("Unable to find file '{}' in available SDK templates.".format(update_file))
                except TypeError:
                    try:
                        copy2(os.path.join(project_template_path, update_file), file_path)
                    except IOError:
                        raise ToolError("Unable to find file '{}' in available SDK3 templates".format(update_file))

        if move_files and "move" in conversion_map[option]:
            for k, v in conversion_map[option]["move"].iteritems():
                self._move_path(k, v)

        os.system('pebble clean')

    def _move_path(self, old_path, new_path, exclude=[]):
        full_path = None
        if isinstance(new_path, dict):
            for k, v in new_path.iteritems():
                if k == "":
                    full_path = v
                else:
                    exclude.append(k)
                    self._move_path(os.path.join(old_path, k), v)
            else:
                if full_path:
                    self._move_path(old_path, full_path, exclude=deepcopy(exclude))
        else:
            if not os.path.exists(old_path):
                print("Path '{}' does not exist and therefore cannot be moved.".format(old_path))
                return

            print("Moving '{}' to '{}'".format(old_path, new_path))
            if os.path.isdir(old_path):
                for item in os.listdir(new_path):
                    if item in exclude:
                        continue
                    if os.path.isdir(item):
                        copytree(old_path, new_path)
                        rmtree(os.path.join(old_path, item))
                    else:
                        copy2(old_path, new_path)
                        os.remove(os.path.join(old_path, item))
            else:
                os.mkdir(os.path.dirname(new_path))
                move(old_path, new_path)

    @classmethod
    def _generate_appinfo_from_old_project(cls, project_root):
        app_info_path = os.path.join(project_root, "appinfo.json")
        if not os.path.exists(app_info_path):
            print("No appinfo.json file exists to convert.")
        with open(app_info_path, "r") as f:
            app_info_json = json.load(f, object_pairs_hook=collections.OrderedDict)

        app_info_json["targetPlatforms"] = pebble_platforms
        app_info_json["sdkVersion"] = "3"

        with open(app_info_path, "w") as f:
            json.dump(app_info_json, f, indent=2, separators=(',', ': '))

    @classmethod
    def add_parser(cls, parser):
        parser = super(PblProjectConverter, cls).add_parser(parser)
        parser.add_argument('--move', action='store_true',
                            help="Update project by moving files that have changed location (experimental).")
        return parser
