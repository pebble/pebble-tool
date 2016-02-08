from __future__ import absolute_import, print_function

import errno
import os

from shutil import copy2
from string import Template
from uuid import uuid4

from . import SDKCommand
from pebble_tool.sdk import SDK_VERSION, sdk_version
from pebble_tool.exceptions import ToolError
from pebble_tool.util.analytics import post_event


class NewProjectCommand(SDKCommand):
    """Creates a new pebble project with the given name in a new directory."""
    command = 'new-project'

    def __call__(self, args):
        super(NewProjectCommand, self).__call__(args)

        # User can give a path to a new project dir
        project_path = args.name
        project_name = os.path.split(project_path)[1]
        project_root = os.path.join(os.getcwd(), project_path)

        project_src = os.path.join(project_root, "src")

        # Create directories
        try:
            os.makedirs(project_root)
            os.makedirs(os.path.join(project_root, "resources"))
            os.makedirs(project_src)
        except OSError as e:
            if e.errno == errno.EEXIST:
                raise ToolError("A directory called '{}' already exists.".format(args.name))
            raise

        project_template_path = os.path.join(self.get_sdk_path(), 'pebble', 'common', 'templates')
        if not os.path.exists(project_template_path):
            project_template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'sdk', 'templates')

        # Create main .c file
        if args.simple:
            default_main = os.path.join(project_template_path, 'simple.c')
        else:
            default_main = os.path.join(project_template_path, 'main.c')
        copy2(default_main, os.path.join(project_src, "{}.c".format(project_name)))

        # Add appinfo.json file
        with open(os.path.join(project_template_path, 'appinfo.json')) as f:
            appinfo = Template(f.read())

        with open(os.path.join(project_root, "appinfo.json"), "w") as f:
            f.write(appinfo.substitute(uuid=str(uuid4()), project_name=project_name, sdk_version=SDK_VERSION))

        # Add .gitignore file
        copy2(os.path.join(project_template_path, 'gitignore'), os.path.join(project_root, '.gitignore'))

        # Add javascript files if applicable
        if args.javascript:
            project_js_src = os.path.join(project_src, "js")
            os.makedirs(project_js_src)

            try:
                copy2(os.path.join(project_template_path, 'app.js'),
                      os.path.join(project_js_src, 'app.js'))
            except IOError as e:
                if e.errno != errno.ENOENT:
                    raise e
                copy2(os.path.join(project_template_path, 'pebble-js-app.js'),
                      os.path.join(project_js_src, 'pebble-js-app.js'))

        # Add background worker files if applicable
        if args.worker:
            project_worker_src = os.path.join(project_root, "worker_src")
            os.makedirs(project_worker_src)
            # Add simple source file
            copy2(os.path.join(project_template_path, 'worker.c'),
                  os.path.join(project_worker_src, "{}_worker.c".format(project_name)))

        # Add wscript file
        if self.sdk == "2.9" or self.sdk is None and sdk_version() == "2.9":
            copy2(os.path.join(project_template_path, 'wscript_sdk2'), os.path.join(project_root, "wscript"))
        else:
            copy2(os.path.join(project_template_path, 'wscript'), os.path.join(project_root, "wscript"))

        post_event("sdk_create_project", javascript=args.javascript, worker=args.worker)
        print("Created new project {}".format(args.name))


    @classmethod
    def add_parser(cls, parser):
        parser = super(NewProjectCommand, cls).add_parser(parser)
        parser.add_argument("name", help="Name of the project you want to create")
        parser.add_argument("--simple", action="store_true", help="Create a minimal C file.")
        parser.add_argument("--javascript", action="store_true", help="Generate a JavaScript file.")
        parser.add_argument("--worker", action="store_true", help="Generate a background worker.")
        return parser
