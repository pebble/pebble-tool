from __future__ import absolute_import, print_function
__author__ = 'katharine'

import argparse
import os
import subprocess
import time

from pebble_tool.exceptions import BuildError
from pebble_tool.util.analytics import post_event
from . import SDKCommand


class BuildCommand(SDKCommand):
    """Builds the current project."""
    command = "build"

    def __call__(self, args):
        super(BuildCommand, self).__call__(args)
        start_time = time.time()
        try:
            waf = list(args.args)
            try:
                waf.remove('--')
            except ValueError:
                pass
            self._waf("configure")
            self._waf("build", *waf)
        except subprocess.CalledProcessError:
            duration = time.time() - start_time
            post_event("app_build_failed", build_time=duration)
            raise BuildError("Build failed.")
        else:
            duration = time.time() - start_time
            has_js = os.path.exists(os.path.join('src', 'js'))
            post_event("app_build_succeeded", has_js=has_js, line_counts=self._get_line_counts(), build_time=duration)

    @classmethod
    def _get_line_counts(cls):
        c_line_count = 0
        js_line_count = 0
        if os.path.exists('src'):
            c_line_count += cls._count_lines('src', ['.h', '.c'])
            js_line_count += cls._count_lines('src', ['.js'])

        return {'c_line_count': c_line_count, 'js_line_count': js_line_count}

    @classmethod
    def _count_lines(cls, path, extensions):
        src_lines = 0
        files = os.listdir(path)
        for name in files:
            if name.startswith('.'):
                continue
            if os.path.isdir(os.path.join(path, name)):
                if not os.path.islink(os.path.join(path, name)):
                    src_lines += cls._count_lines(os.path.join(path, name), extensions)
                continue
            ext = os.path.splitext(name)[1]
            if ext in extensions:
                src_lines += sum(1 for line in open(os.path.join(path, name)))
        return src_lines

    @classmethod
    def add_parser(cls, parser):
        parser = super(BuildCommand, cls).add_parser(parser)
        parser.add_argument('args', nargs=argparse.REMAINDER, help="Extra arguments to pass to waf.")
        return parser


class CleanCommand(SDKCommand):
    command = "clean"

    def __call__(self, args):
        super(CleanCommand, self).__call__(args)
        try:
            self._waf("distclean")
        except subprocess.CalledProcessError:
            print("Clean failed.")
