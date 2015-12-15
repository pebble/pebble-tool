__author__ = 'katharine'

import re

_version_parser = re.compile(r"^([0-9]+)(?:\.([0-9]+))?(?:\.([0-9]+))?(?:\-(beta|rc|dp)([0-9]+))?")


def version_to_key(version):
    result = _version_parser.match(version)
    if result is None:
        return (0, 0, 0, 0, 0, version)
    suffix_mapping = {
        'dp': -3,
        'beta': -2,
        'rc': -1,
        None: 0,
    }

    return (int(result.group(1)),
            int(result.group(2) or 0),
            int(result.group(3) or 0),
            suffix_mapping[result.group(4)],
            int(result.group(5) or 0),
            "")
