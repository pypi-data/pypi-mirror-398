class ClientException(Exception):
    pass


class DatasetExists(ClientException):
    pass


class ExperimentExists(ClientException):
    pass


class InterpretationExists(ClientException):
    pass


class ExplainerNotFound(ClientException):
    pass


class ProjectExists(ClientException):
    pass


class NotSupportedByServer(ClientException):
    pass


# If we're not able to communicate with the DAI
# server, this exception is thrown.
class ServerDownException(ClientException):
    pass


class ServerLicenseInvalid(ClientException):
    pass


class ServerVersionExtractionFailed(ClientException):
    pass


class ServerVersionNotSupported(ClientException):
    pass


class InvalidOperationException(ClientException):
    """Raised when an invalid operation is attempted."""

    pass


class InvalidStateException(ClientException):
    """Raised when an invalid state is encountered."""

    pass
