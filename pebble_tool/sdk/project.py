from __future__ import print_function

__author__ = 'katharine'

import json
from jsonschema import Draft4Validator, RefResolver, ValidationError
import os
import os.path
import uuid

SDK_VERSION = "3"

from pebble_tool.exceptions import (InvalidProjectException, InvalidJSONException, OutdatedProjectException,
                                    PebbleProjectException)
from pebble_tool.sdk import sdk_version, sdk_path
from . import pebble_platforms


class PebbleProject(object):
    def __new__(cls, project_dir=None):
        if project_dir is None:
            project_dir = os.getcwd()
        if NpmProject.should_process(project_dir):
            return NpmProject(project_dir)
        else:
            return AppinfoProject(project_dir)

    def __init__(self, project_dir=None):
        if project_dir is None:
            project_dir = os.getcwd()
        self.project_dir = project_dir
        self.check_project_directory(self.project_dir)
        self._parse_project()
        self._sanity_check()

    def _sanity_check(self):
        """Check to see if the current directory matches what is created by PblProjectCreator.run.

        Raises an InvalidProjectException or an OutdatedProjectException if everything isn't quite right.
        """

        if self.project_type not in  ('native', 'package', 'rocky'):
            if self.project_type == 'pebblejs':
                raise InvalidProjectException("Pebble.js is not part of the pebble SDK, and so the SDK can't build it.\n"
                                              "Either use CloudPebble or follow the instructions at "
                                              "https://github.com/pebble/pebblejs/blob/master/README.md#getting-started")
            else:
                raise InvalidProjectException("Unsupported project type '%s'." % self.project_type)

        if os.path.islink(os.path.join(self.project_dir, 'pebble_app.ld')) \
                or os.path.exists(os.path.join(self.project_dir, 'resources/src/resource_map.json')) \
                or not os.path.exists(os.path.join(self.project_dir, 'wscript')):
            raise OutdatedProjectException("This project is very outdated, and cannot be handled by this SDK.")

        if self.sdk_version == '2.9':
            if sdk_version() != '2.9':
                raise OutdatedProjectException("This projected is outdated (try 'pebble convert-project' or"
                                               "'pebble sdk install 2.9')")
        elif self.sdk_version != SDK_VERSION:
            raise PebbleProjectException("An invalid value of '{}' was found in the 'sdkVersion' field of the "
                                         "project's package.json. The latest supported value for this field is '{}'.".
                                         format(self.sdk_version, SDK_VERSION))

    def _parse_project(self):
        raise NotImplementedError

    @staticmethod
    def check_project_directory(project_dir):
        _validate_project_json(project_dir)
        if not os.path.isdir(os.path.join(project_dir, 'src')):
            raise InvalidProjectException("This is not a project directory.")
        if not os.path.exists(os.path.join(project_dir, 'wscript')):
            raise OutdatedProjectException("This project is missing a wscript file and cannot be handled by the SDK.")


class AppinfoProject(PebbleProject):
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls, *args, **kwargs)

    @staticmethod
    def should_process(project_dir):
        return os.path.exists(os.path.join(project_dir, 'appinfo.json'))

    def _parse_project(self):
        with open(os.path.join(self.project_dir, 'appinfo.json')) as f:
            self.appinfo = json.load(f)

        self.uuid = uuid.UUID(self.appinfo['uuid'])
        self.short_name = self.appinfo['shortName']
        self.long_name = self.appinfo['longName']
        self.company_name = self.appinfo['companyName']
        self.version = self.appinfo['versionLabel']
        self.sdk_version = self.appinfo.get('sdkVersion', 2)
        self.target_platforms = self.appinfo.get('targetPlatforms', pebble_platforms)
        self.enable_multi_js = self.appinfo.get('enableMultiJS', False)
        self.capabilities = self.appinfo.get('capabilities', [])
        self.project_type = self.appinfo.get('projectType', 'native')
        self.resources = self.appinfo.get('resources', {})
        self.message_keys = self.appinfo.get('appKeys', {})
        self.dependencies = {}

        watchapp = self.appinfo.get('watchapp', {})
        self.is_watchface = watchapp.get('watchface', False)
        self.is_hidden = watchapp.get('hiddenApp', False)
        self.is_shown_only_on_communication = watchapp.get('onlyShownOnCommunication', False)


class NpmProject(PebbleProject):
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls, *args, **kwargs)

    @staticmethod
    def should_process(project_dir):
        _validate_project_json(project_dir)
        package_json_path = os.path.join(project_dir, 'package.json')
        if os.path.exists(package_json_path):
            with open(os.path.join(project_dir, 'package.json')) as f:
                if 'pebble' in json.load(f):
                    return True
        return False

    def _parse_project(self):
        with open(os.path.join(self.project_dir, 'package.json')) as f:
            self.project_info = json.load(f)

        self.appinfo = self.project_info['pebble']
        self.short_name = self.project_info['name']
        self.company_name = self.project_info['author']
        self.version = self.project_info['version']
        self.sdk_version = self.appinfo.get('sdkVersion', 2)
        self.target_platforms = self.appinfo.get('targetPlatforms', pebble_platforms)
        self.enable_multi_js = self.appinfo.get('enableMultiJS', False)
        self.capabilities = self.appinfo.get('capabilities', [])
        self.project_type = self.appinfo.get('projectType', 'native')
        self.dependencies = self.project_info.get('dependencies', {})
        self.dependencies.update(self.project_info.get('devDependencies', {}))
        self.resources = self.appinfo.get('resources', {})
        self.message_keys = self.appinfo.get('messageKeys', {})
        if self.project_type != 'package':
            if 'uuid' not in self.appinfo:
                raise InvalidProjectException("This project doesn't have a UUID, but appears to be an app. "
                                              "Did you miss a 'projectType'?")
            self.long_name = self.appinfo.get('displayName', self.short_name)
            self.uuid = uuid.UUID(self.appinfo['uuid'])
            watchapp = self.appinfo.get('watchapp', {})
            self.is_watchface = watchapp.get('watchface', False)
            self.is_hidden = watchapp.get('hiddenApp', False)
            self.is_shown_only_on_communication = watchapp.get('onlyShownOnCommunication', False)
        else:
            self.uuid = None
            self.is_watchface = False
            self.is_hidden = False
            self.is_shown_only_on_communication = False
            self.long_name = self.short_name


def _validate_project_json(project_dir):
    package_json_path = os.path.join(project_dir, 'package.json')
    appinfo_json_path = os.path.join(project_dir, 'appinfo.json')

    try:
        with open(package_json_path, 'r') as f:
            try:
                info = json.load(f)
            except ValueError as e:
                raise InvalidJSONException("package.json file does not contain valid JSON:\n{}".format(e))
            else:
                if 'pebble' not in info:
                    raise IOError
    except IOError:
        try:
            with open(appinfo_json_path, 'r') as f:
                try:
                    info = json.load(f)
                except ValueError as e:
                    raise InvalidJSONException("appinfo.json file does not contain valid JSON:\n{}".format(e))
        except IOError:
            raise InvalidProjectException("Unable to find package.json file.")
        else:
            _validate_with_schema(info, "appinfo.json")
    else:
        _validate_with_schema(info, "package.json")


def _validate_with_schema(json_info, filetype):
    try:
        _get_json_schema_validator(filetype).validate(json_info)
    except ValidationError as e:
        error_message = "Unable to validate {} due to one of the following reasons:\n".format(filetype)
        for error in [e] + e.context:
            if error.absolute_path:
                absolute_path = '.'.join([str(path) for path in list(error.absolute_path)])
                error_message += "- {}: {}\n".format(absolute_path, error.message)
            else:
                error_message += "- {}\n".format(error.message)
        raise InvalidJSONException(error_message)


def _get_json_schema_validator(json_filetype):
    schema_path = os.path.join(sdk_path(), 'pebble', 'common', 'tools', 'schemas', json_filetype)
    if os.path.exists(schema_path):
        resolver = RefResolver('file://' + os.path.dirname(schema_path) + '/', os.path.basename(schema_path))
        with open(schema_path, "r") as f:
            return Draft4Validator(json.load(f), resolver=resolver)
    return Draft4Validator({})


def check_current_directory():
    return PebbleProject.check_project_directory(os.getcwd())


def requires_project_dir(func):
    def wrapper(self, args):
        check_current_directory()
        return func(self, args)
    return wrapper
