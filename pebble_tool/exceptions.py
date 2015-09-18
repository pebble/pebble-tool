__author__ = 'katharine'


class ToolError(Exception):
    pass


class MissingSDK(ToolError):
    pass


class MissingEmulatorError(MissingSDK):
    pass


class BuildError(ToolError):
    pass


class PebbleProjectException(ToolError):
    pass


class InvalidProjectException(PebbleProjectException):
    pass


class InvalidJSONException(PebbleProjectException):
    pass


class OutdatedProjectException(PebbleProjectException):
    pass

class SDKInstallError(ToolError):
    pass
