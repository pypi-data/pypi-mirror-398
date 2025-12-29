"""Joblet SDK exceptions."""


class JobletException(Exception):
    """Base exception for all Joblet SDK errors."""

    pass


class ConnectionError(JobletException):
    """Can't connect to server."""

    pass


class AuthenticationError(JobletException):
    """Authentication failed."""

    pass


class JobNotFoundError(JobletException):
    """Job not found."""

    pass


class RuntimeNotFoundError(JobletException):
    """Runtime not found."""

    pass


class NetworkError(JobletException):
    """Network operation failed."""

    pass


class VolumeError(JobletException):
    """Volume operation failed."""

    pass


class ValidationError(JobletException):
    """Invalid input."""

    pass


class TimeoutError(JobletException):
    """Operation timed out."""

    pass
