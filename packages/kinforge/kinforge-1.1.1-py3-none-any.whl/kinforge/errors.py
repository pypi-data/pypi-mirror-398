class KinforgeError(Exception):
    """Base class for all Kinforge errors."""


class SchemaValidationError(KinforgeError):
    pass


class CompileError(KinforgeError):
    pass


class ExportError(KinforgeError):
    pass
