__author__ = 'katharine'


class ToolError(Exception):
    pass


class MissingSDK(ToolError):
    pass


class MissingEmulatorError(MissingSDK):
    pass
