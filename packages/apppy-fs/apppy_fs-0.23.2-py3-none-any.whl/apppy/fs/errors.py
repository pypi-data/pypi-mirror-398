from apppy.fastql.annotation import fastql_type_error
from apppy.fastql.errors import GraphQLClientError, GraphQLServerError


@fastql_type_error
class FileSystemInvalidProtocolError(GraphQLServerError):
    """Raised when a FileSystem encounters a protocol which it does not support"""

    protocol: str

    def __init__(self, protocol: str):
        super().__init__("file_system_invalid_protocol")
        self.protocol = protocol


@fastql_type_error
class FileSystemPermissionsError(GraphQLClientError):
    """Raised when a FileSystem does not have the correct permissions"""

    def __init__(self, code: str):
        super().__init__(code)


@fastql_type_error
class FileSystemNotFoundError(GraphQLClientError):
    """Raised when a FileSystem cannot be found"""

    protocol: str

    def __init__(self, protocol: str):
        super().__init__("file_system_not_found")
        self.protocol = protocol


@fastql_type_error
class FileSystemSizeLimitExceededError(GraphQLClientError):
    """Raised when a FileSystem size limit is exceeded"""

    file_size: int
    file_size_max: int

    def __init__(self, file_size: int, file_size_max: int):
        super().__init__("file_system_size_limit_exceeded")
        self.file_size = file_size
        self.file_size_max = file_size_max


@fastql_type_error
class MalformedFileUrlError(GraphQLClientError):
    """Raised when a file url is malformed"""

    url: str

    def __init__(self, url: str, code: str | None = None):
        super().__init__(code if code is not None else "malformed_file_url")
        self.url: str
