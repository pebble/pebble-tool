__author__ = 'katharine'

import json
import os
import os.path
import uuid

SDK_VERSION = "3"

from pebble_tool.exceptions import InvalidProjectException, InvalidJSONException, OutdatedProjectException


class PebbleProject(object):
    def __init__(self, project_dir=None):
        self.project_dir = project_dir if project_dir is not None else os.getcwd()
        self.check_project_directory(self.project_dir)
        self._parse_project()

    @staticmethod
    def check_project_directory(project_dir):
        """Check to see if the current directory matches what is created by PblProjectCreator.run.

        Raises an InvalidProjectException or an OutdatedProjectException if everything isn't quite right.
        """

        if not os.path.isdir(os.path.join(project_dir, 'src')):
            raise InvalidProjectException("This is not a project directory.")

        try:
            with open(os.path.join(project_dir, "appinfo.json"), "r") as f:
                try:
                    app_info = json.load(f)
                except ValueError as ex:
                    raise InvalidJSONException("Could not parse appinfo.json because of the following error: %s" % ex)
        except IOError:
            raise InvalidProjectException("Couldn't open project info.")

        if os.path.islink(os.path.join(project_dir, 'pebble_app.ld')) \
                or os.path.exists(os.path.join(project_dir, 'resources/src/resource_map.json')) \
                or not os.path.exists(os.path.join(project_dir, 'wscript')) \
                or 'sdkVersion' not in app_info \
                or app_info.get("sdkVersion", None) != SDK_VERSION:
            raise OutdatedProjectException("This project is outdated (try 'pebble convert-project').")

    def _parse_project(self):
        with open(os.path.join(self.project_dir, 'appinfo.json')) as f:
            self.appinfo = json.load(f)

        self.uuid = uuid.UUID(self.appinfo['uuid'])
        self.short_name = self.appinfo['shortName']
        self.long_name = self.appinfo['longName']
        self.company_name = self.appinfo['companyName']
        self.version = self.appinfo['versionLabel']
        self.sdk_version = self.appinfo['sdkVersion']
        self.target_platforms = self.appinfo.get('targetPlatforms', ['aplite', 'basalt'])
        self.capabilities = self.appinfo.get('capabilities', [])

        watchapp = self.appinfo.get('watchapp', {})
        self.is_watchface = watchapp.get('watchface', False)
        self.is_hidden = watchapp.get('hiddenApp', False)
        self.is_shown_only_on_communication = watchapp.get('onlyShownOnCommunication', False)


def check_current_directory():
    return PebbleProject.check_project_directory(os.getcwd())


def requires_project_dir(func):
    def wrapper(self, args):
        check_current_directory()
        return func(self, args)
    return wrapper
