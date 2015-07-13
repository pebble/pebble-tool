from __future__ import print_function
import colors
from functools import partial
import sys

LOG_LEVEL_ALWAYS = 0
LOG_LEVEL_ERROR = 1
LOG_LEVEL_WARNING = 50
LOG_LEVEL_INFO = 100
LOG_LEVEL_DEBUG = 200
LOG_LEVEL_DEBUG_VERBOSE = 255


class ColorScheme(object):
    """ A context-manager class which colourises all `print' output
     inside the context """
    schemes = []
    old_stdout = None

    def __init__(self, level):
        self.level = level
        self.scheme = {
            LOG_LEVEL_ALWAYS: lambda x: x,
        }

    def __enter__(self):
        if ColorScheme.old_stdout is None:
            ColorScheme.old_stdout = sys.stdout
            sys.stdout = self
        ColorScheme.schemes.append(self)

    def __exit__(self, the_type, value, traceback):
        ColorScheme.schemes.pop()
        if len(ColorScheme.schemes) == 0:
            sys.stdout = ColorScheme.old_stdout
            ColorScheme.old_stdout = None

    @staticmethod
    def write(message):
        current_scheme = ColorScheme.schemes[-1]
        func = None
        for k in sorted(current_scheme.scheme.keys(), reverse=True):
            if current_scheme.level >= k:
                func = current_scheme.scheme[k]
                break

        ColorScheme.old_stdout.write(func(message))


class DefaultColors(ColorScheme):
    """ Default colour scheme """
    def __init__(self, level):
        super(DefaultColors, self).__init__(level)
        self.scheme.update({
            LOG_LEVEL_ERROR: partial(colors.color, fg='red', style='negative'),
            LOG_LEVEL_WARNING: colors.red,
            LOG_LEVEL_INFO: colors.black,
            LOG_LEVEL_DEBUG: colors.green,
            LOG_LEVEL_DEBUG_VERBOSE: colors.cyan
        })


class WatchColors(DefaultColors):
    """ Special colours for the watch """
    def __init__(self, level):
        super(WatchColors, self).__init__(level)
        self.scheme.update({
            LOG_LEVEL_INFO: colors.magenta,
            LOG_LEVEL_DEBUG: colors.blue,
        })
