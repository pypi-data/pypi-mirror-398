"""Custom exceptions for the Hegel IP client library."""


class HegelError(Exception):
    """Base class for all Hegel client library errors."""


class HegelConnectionError(HegelError):
    """Error raised when connection to the Hegel device fails or drops.

    This exception is raised when:
    - The initial connection to the device cannot be established
    - The connection is unexpectedly closed or reset
    - Network-related errors occur during communication
    """
