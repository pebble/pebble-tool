from __future__ import absolute_import, print_function

import errno
import os
import uuid

from ..base import BaseCommand
from pebble_tool.exceptions import ToolError
from pebble_tool.sdk.templates import (FILE_SIMPLE_MAIN, FILE_DUMMY_MAIN, FILE_DUMMY_APPINFO, DICT_DUMMY_APPINFO,
                                       FILE_GITIGNORE, FILE_DUMMY_JAVASCRIPT_SRC, FILE_WSCRIPT, FILE_DUMMY_WORKER)
from pebble_tool.util.analytics import post_event


class NewProjectCommand(BaseCommand):
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

        # Create main .c file
        with open(os.path.join(project_src, "{}.c".format(project_name)), "w") as f:
            f.write(FILE_SIMPLE_MAIN if args.simple else FILE_DUMMY_MAIN)

        # Add appinfo.json file
        appinfo_dummy = DICT_DUMMY_APPINFO.copy()
        appinfo_dummy['uuid'] = str(uuid.uuid4())
        appinfo_dummy['project_name'] = project_name
        with open(os.path.join(project_root, "appinfo.json"), "w") as f:
            f.write(FILE_DUMMY_APPINFO.substitute(**appinfo_dummy))

        # Add .gitignore file
        with open(os.path.join(project_root, ".gitignore"), "w") as f:
            f.write(FILE_GITIGNORE)

        # Add javascript files if applicable
        if args.javascript:
            project_js_src = os.path.join(project_src, "js")
            os.makedirs(project_js_src)

            with open(os.path.join(project_js_src, "pebble-js-app.js"), "w") as f:
                f.write(FILE_DUMMY_JAVASCRIPT_SRC)

        # Add background worker files if applicable
        if args.worker:
            project_worker_src = os.path.join(project_root, "worker_src")
            os.makedirs(project_worker_src)
            # Add simple source file
            with open(os.path.join(project_worker_src, "{}_worker.c".format(project_name)), "w") as f:
                f.write(FILE_DUMMY_WORKER)

        # Add wscript file
        with open(os.path.join(project_root, "wscript"), "w") as f:
            f.write(FILE_WSCRIPT)

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
