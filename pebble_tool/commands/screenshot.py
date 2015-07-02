from __future__ import absolute_import, print_function
__author__ = 'katharine'

import datetime
import png
import os.path
from progressbar import ProgressBar, Bar, ReverseBar, FileTransferSpeed, Timer, Percentage
import subprocess
import sys

from libpebble2.services.screenshot import Screenshot

from .base import BaseCommand


class ScreenshotCommand(BaseCommand):
    """Takes a screenshot from the watch."""
    command = 'screenshot'

    def __init__(self):
        self.progress_bar = ProgressBar(widgets=[Percentage(), Bar(marker='=', left='[', right=']'), ' ',
                                                 FileTransferSpeed(), ' ', Timer(format='%s')])
        self.started = False

    def __call__(self, args):
        super(ScreenshotCommand, self).__call__(args)
        pebble = self._connect(args)
        screenshot = Screenshot(pebble)
        screenshot.register_handler("progress", self._handle_progress)

        self.progress_bar.start()
        image = screenshot.grab_image()
        self.progress_bar.finish()

        filename = self._generate_filename() if args.filename is None else args.filename
        png.from_array(image, mode='RGB8').save(filename)
        print("Saved screenshot to {}".format(filename))
        self._open(os.path.abspath(filename))

    def _handle_progress(self, progress, total):
        if not self.started:
            self.progress_bar.maxval = total
            self.started = True
        self.progress_bar.update(progress)

    @classmethod
    def _generate_filename(cls):
        return datetime.datetime.now().strftime("pebble_screenshot_%Y-%m-%d_%H-%M-%S.png")

    @classmethod
    def _open(cls, path):
        if sys.platform == 'darwin':
            subprocess.call(["open", path])

    @classmethod
    def add_parser(cls, parser):
        parser = super(ScreenshotCommand, cls).add_parser(parser)
        parser.add_argument('filename', nargs='?', type=str, help="Filename of screenshot")
        return parser
