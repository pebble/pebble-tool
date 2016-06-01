# encoding: utf-8
from __future__ import absolute_import, print_function

import subprocess

from . import SDKProjectCommand
from pebble_tool.exceptions import ToolError
import pebble_tool.util.npm as npm

__author__ = "katharine"


class PackageManager(SDKProjectCommand):
    """Manages available SDKs"""
    command = 'package'
    has_subcommands = True

    def __call__(self, args):
        super(PackageManager, self).__call__(args)
        args.sub_func(args)

    @classmethod
    def add_parser(cls, parser):
        parser = super(PackageManager, cls).add_parser(parser)
        subparsers = parser.add_subparsers(title="subcommand")

        install_parser = subparsers.add_parser("install", help="Installs the given SDK.")
        install_parser.add_argument('package', nargs='?', help="npm package to install.")
        install_parser.set_defaults(sub_func=cls.do_install)

        uninstall_parser = subparsers.add_parser("uninstall", help="Uninstalls the given SDK.")
        uninstall_parser.add_argument('package', help="package to uninstall.")
        uninstall_parser.set_defaults(sub_func=cls.do_uninstall)

        return parser

    @classmethod
    def do_install(cls, args):
        try:
            npm.invoke_npm(["install", "--save", "--ignore-scripts", args.package])
            npm.invoke_npm(["dedupe"])
            npm.sanity_check()
        except subprocess.CalledProcessError:
            raise ToolError()

    @classmethod
    def do_uninstall(cls, args):
        npm.invoke_npm(["uninstall", "--save", "--ignore-scripts", args.package])
