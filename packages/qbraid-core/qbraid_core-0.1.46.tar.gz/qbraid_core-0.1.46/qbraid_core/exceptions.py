# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module defining custom exceptions for the qBraid CORE.

"""

from typing import Optional

DEFAULT_ERROR_MESSAGE = (
    "An unexpected error occurred while processing your qBraid command. "
    "Please check your input and try again. If the problem persists, "
    "visit https://github.com/qBraid/community/issues to file a bug report."
)


class QbraidException(Exception):
    """Custom exception class for qBraid core errors."""

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = DEFAULT_ERROR_MESSAGE
        super().__init__(message)


class QbraidChainedException(Exception):
    """Custom exception class to handle multiple underlying exceptions."""

    def __init__(self, message: Optional[str] = None, exceptions: Optional[list[Exception]] = None):
        if message is None:
            message = "Multiple errors occurred."
        super().__init__(message)
        self.exceptions = exceptions or []

    def add_exception(self, exc: Exception):
        """Add an exception to the chain."""
        self.exceptions.append(exc)


class AuthError(QbraidException):
    """Base class for errors raised authorizing user"""


class ConfigError(QbraidException):
    """Base class for errors raised while setting a user configuartion"""


class RequestsApiError(QbraidException):
    """Exception re-raising a RequestException."""


class ResourceNotFoundError(QbraidException):
    """Exception re-raising a RequestException."""


class UserNotFoundError(ResourceNotFoundError):
    """Exception raised when a user is not found."""
