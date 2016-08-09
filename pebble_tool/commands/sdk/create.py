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


def _copy_template(name, directory_list, appinfo_list, file_list, create_dir_list):
    try:
        project_path = name
        project_name = os.path.split(project_path)[1]
        project_root = os.path.join(os.getcwd(), project_path)
        os.mkdir(project_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            raise ToolError("A directory called '{}' already exists.".format(project_name))
        raise

    for directory in directory_list:
        if os.path.exists(directory):
            template_path = directory
            break
    else:
        raise ToolError("Can't create that sort of project with the current SDK.")

    for appinfo_path in appinfo_list:
        appinfo_path = os.path.join(template_path, appinfo_path)
        if os.path.exists(appinfo_path):
            file_list.append((appinfo_path, os.path.join(project_root, os.path.basename(appinfo_path))))
            break
    else:
        raise ToolError("Couldn't find an appinfo-like file.")

    for file_path in file_list:
        if isinstance(file_path, basestring):
            origin_path = os.path.join(template_path, file_path)
            target_path = os.path.join(project_root, file_path)
        else:
            origin_path = os.path.join(template_path, file_path[0])
            target_path = os.path.join(project_root, file_path[1])

        if os.path.exists(origin_path):
            try:
                os.makedirs(os.path.dirname(target_path))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            with open(origin_path) as f:
                template = Template(f.read())
            with open(target_path, 'w') as f:
                f.write(template.substitute(uuid=str(uuid4()),
                                            project_name=project_name,
                                            display_name=project_name,
                                            sdk_version=SDK_VERSION))


class NewProjectCommand(SDKCommand):
    """Creates a new pebble project with the given name in a new directory."""
    command = 'new-project'

    def __call__(self, args):
        super(NewProjectCommand, self).__call__(args)

        project_path = args.name
        project_name = os.path.split(project_path)[1]
        sdk2 = self.sdk == "2.9" or (self.sdk is None and sdk_version() == "2.9")

        file_list = [('gitignore', '.gitignore')]
        if args.rocky:
            if sdk2:
                raise ToolError("--rocky is not compatible with SDK 2.9")
            if args.simple or args.worker:
                raise ToolError("--rocky is incompatible with --simple and --worker")
            template_paths = [os.path.join(self.get_sdk_path(), 'pebble', 'common', 'templates', 'rocky')]
            file_list.extend([
                ('app.js', 'src/pkjs/app.js'),
                ('index.js', 'src/rocky/index.js'),
                ('wscript', 'wscript')
            ])
        else:
            template_paths = [
                os.path.join(self.get_sdk_path(), 'pebble', 'common', 'templates', 'app'),
                os.path.join(self.get_sdk_path(), 'pebble', 'common', 'templates'),
                os.path.join(os.path.dirname(__file__), '..', '..', 'sdk', 'templates')
            ]
            file_list.extend([
                ('simple.c' if args.simple else 'main.c', 'src/c/{}.c'.format(project_name)),
                ('wscript_sdk2' if sdk2 else 'wscript', 'wscript')
            ])

            if args.javascript:
                file_list.extend([('app.js', 'src/js/app.js'), ('pebble-js-app.js', 'src/js/pebble-js-app.js')])
            if args.worker:
                file_list.append(('worker.c', 'worker_src/c/{}_worker.c'.format(project_name)))

        _copy_template(args.name, template_paths, ['package.json', 'appinfo.json'], file_list, ['resources'])

        post_event("sdk_create_project", javascript=args.javascript or args.rocky, worker=args.worker, rocky=args.rocky)
        print("Created new project {}".format(args.name))

    @classmethod
    def add_parser(cls, parser):
        parser = super(NewProjectCommand, cls).add_parser(parser)
        parser.add_argument("name", help="Name of the project you want to create")
        type_group = parser.add_argument_group("project type")
        exclusive_type_group = type_group.add_mutually_exclusive_group()
        exclusive_type_group.add_argument("--rocky", action="store_true", help="Create a Rocky.js project.")
        exclusive_type_group.add_argument("--c", action="store_true", help="Create a C project.")
        c_group = parser.add_argument_group('C-specific arguments')
        c_group.add_argument("--simple", action="store_true", help="Create a minimal C file.")
        c_group.add_argument("--javascript", action="store_true", help="Generate a JavaScript file.")
        c_group.add_argument("--worker", action="store_true", help="Generate a background worker.")
        return parser


class NewPackageCommand(SDKCommand):
    """Creates a new pebble package (not app or watchface) with the given name in a new directory."""
    command = 'new-package'

    def __call__(self, args):
        super(NewPackageCommand, self).__call__(args)

        package_path = args.name
        package_name = os.path.split(package_path)[1]

        template_paths = [
            os.path.join(self.get_sdk_path(), 'pebble', 'common', 'templates', 'lib'),
        ]
        file_list = [
            ('gitignore', '.gitignore'),
            ('lib.c', 'src/c/{}.c'.format(package_name)),
            ('lib.h', 'include/{}.h'.format(package_name)),
            'wscript',
        ]
        dir_list = ['src/resources']
        if args.javascript:
            file_list.append(('lib.js', 'src/js/index.js'))

        _copy_template(args.name, template_paths, ['package.json'], file_list, dir_list)

        post_event("sdk_create_package", javascript=args.javascript)
        print("Created new package {}".format(args.name))

    @classmethod
    def add_parser(cls, parser):
        parser = super(NewPackageCommand, cls).add_parser(parser)
        parser.add_argument("name", help="Name of the package you want to create")
        parser.add_argument("--javascript", action="store_true", help="Include a js directory.")
        return parser
