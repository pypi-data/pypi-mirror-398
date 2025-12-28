"""Custom exceptions for datastore operations."""


class DatastoreError(Exception):
    """Base exception for all datastore operations."""

    pass


class DatastoreConfigError(DatastoreError):
    """Exception raised when datastore configuration is invalid."""

    pass


class DatastoreOperationError(DatastoreError):
    """Exception raised when a datastore operation fails."""

    pass


class ProxyInvocationError(DatastoreError):
    """Exception raised when proxy Lambda invocation fails."""

    pass
