from __future__ import absolute_import, print_function
__author__ = 'katharine'

import datetime
import itertools
import png
import os.path
from progressbar import ProgressBar, Bar, ReverseBar, FileTransferSpeed, Timer, Percentage
import subprocess
import sys

from libpebble2.services.screenshot import Screenshot

from .base import PebbleCommand


class ScreenshotCommand(PebbleCommand):
    """Takes a screenshot from the watch."""
    command = 'screenshot'

    def __init__(self):
        self.progress_bar = ProgressBar(widgets=[Percentage(), Bar(marker='=', left='[', right=']'), ' ',
                                                 FileTransferSpeed(), ' ', Timer(format='%s')])
        self.started = False

    def __call__(self, args):
        super(ScreenshotCommand, self).__call__(args)
        screenshot = Screenshot(self.pebble)
        screenshot.register_handler("progress", self._handle_progress)

        self.progress_bar.start()
        image = screenshot.grab_image()
        if not args.no_correction:
            image = self._correct_colours(image)
        self.progress_bar.finish()

        filename = self._generate_filename() if args.filename is None else args.filename
        png.from_array(image, mode='RGB;8').save(filename)
        print("Saved screenshot to {}".format(filename))
        self._open(os.path.abspath(filename))

    def _handle_progress(self, progress, total):
        if not self.started:
            self.progress_bar.maxval = total
            self.started = True
        self.progress_bar.update(progress)

    def _correct_colours(self, image):
        mapping = {
            (0, 0, 0): (0, 0, 0),
            (0, 0, 85): (27, 22, 74),
            (0, 0, 170): (63, 53, 153),
            (0, 0, 255): (98, 84, 227),
            (0, 85, 0): (44, 74, 43),
            (0, 85, 85): (54, 78, 86),
            (0, 85, 170): (77, 91, 157),
            (0, 85, 255): (107, 110, 230),
            (0, 170, 0): (96, 152, 94),
            (0, 170, 85): (100, 154, 117),
            (0, 170, 170): (114, 160, 175),
            (0, 170, 255): (134, 170, 241),
            (0, 255, 0): (145, 227, 142),
            (0, 255, 85): (148, 229, 158),
            (0, 255, 170): (157, 232, 201),
            (0, 255, 255): (171, 238, 255),
            (85, 0, 0): (65, 30, 0),
            (85, 0, 85): (72, 39, 72),
            (85, 0, 170): (90, 62, 152),
            (85, 0, 255): (116, 88, 226),
            (85, 85, 0): (79, 81, 39),
            (85, 85, 85): (84, 84, 84),
            (85, 85, 170): (100, 96, 157),
            (85, 85, 255): (124, 114, 230),
            (85, 170, 0): (114, 155, 92),
            (85, 170, 85): (118, 157, 117),
            (85, 170, 170): (130, 163, 174),
            (85, 170, 255): (147, 173, 241),
            (85, 255, 0): (158, 230, 142),
            (85, 255, 85): (160, 231, 157),
            (85, 255, 170): (167, 234, 201),
            (85, 255, 255): (181, 241, 255),
            (170, 0, 0): (135, 67, 0),
            (170, 0, 85): (138, 72, 64),
            (170, 0, 170): (148, 86, 149),
            (170, 0, 255): (163, 106, 225),
            (170, 85, 0): (141, 99, 22),
            (170, 85, 85): (144, 103, 79),
            (170, 85, 170): (153, 112, 154),
            (170, 85, 255): (167, 127, 227),
            (170, 170, 0): (162, 165, 87),
            (170, 170, 85): (164, 166, 113),
            (170, 170, 170): (171, 171, 171),
            (170, 170, 255): (184, 181, 239),
            (170, 255, 0): (192, 235, 138),
            (170, 255, 85): (194, 236, 155),
            (170, 255, 170): (200, 240, 199),
            (170, 255, 255): (211, 246, 255),
            (255, 0, 0): (202, 104, 0),
            (255, 0, 85): (204, 107, 47),
            (255, 0, 170): (210, 116, 143),
            (255, 0, 255): (220, 131, 222),
            (255, 85, 0): (206, 125, 0),
            (255, 85, 85): (208, 128, 65),
            (255, 85, 170): (213, 135, 149),
            (255, 85, 255): (223, 148, 225),
            (255, 170, 0): (219, 180, 76),
            (255, 170, 85): (221, 181, 105),
            (255, 170, 170): (226, 186, 167),
            (255, 170, 255): (235, 195, 236),
            (255, 255, 0): (241, 245, 132),
            (255, 255, 85): (242, 246, 149),
            (255, 255, 170): (247, 249, 195),
            (255, 255, 255): (255, 255, 255),
        }
        return [list(itertools.chain(*[mapping[y[x], y[x+1], y[x+2]] for x in xrange(0, len(y), 3)])) for y in image]

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
        parser.add_argument('--no-correction', action="store_true", help="Disable colour correction.")
        return parser
