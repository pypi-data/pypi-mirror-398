"""
Custom exceptions for ClickZetta bulk load operations.
"""


class UnsupportedOperationException(Exception):
    """Exception raised when an operation is not supported."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class BulkLoadException(Exception):
    """Base exception for bulk load operations."""

    def __init__(self, message: str, cause: Exception = None):
        self.message = message
        self.cause = cause
        super().__init__(self.message)


class TableNotFoundException(BulkLoadException):
    """Exception raised when a table is not found."""
    pass


class InvalidFormatException(BulkLoadException):
    """Exception raised when an invalid format is specified."""
    pass
