"""Request-related constants for datastore operations."""

from typing import Final


class REQUEST_TYPE:
    """Request type constants for datastore operations."""

    GET_ITEM: Final[str] = "getItem"
    PUT_ITEM: Final[str] = "putItem"
    QUERY: Final[str] = "query"
    DELETE_ITEM: Final[str] = "deleteItem"


class RESULT_STATUS:
    """Result status constants for datastore operations."""

    SUCCESS: Final[str] = "success"
    FAIL: Final[str] = "fail"
