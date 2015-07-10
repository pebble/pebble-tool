import colors
from functools import partial


class Color(object):
    watch_log = colors.blue
    phone_log = colors.magenta
    crash_info = partial(colors.color, fg='red', style='negative')
    crash = colors.red
