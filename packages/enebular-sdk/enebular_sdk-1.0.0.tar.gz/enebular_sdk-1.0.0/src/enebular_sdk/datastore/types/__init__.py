"""Type definitions for datastore operations."""

from typing import Any, Dict, List, Optional, TypedDict, Union


# Configuration types


class DatastoreConfig(TypedDict, total=False):
    """Configuration for the datastore client."""

    jwt: Optional[str]
    proxy_arn: Optional[str]


# Internal types (not exported in __all__)


class _ExecuteGetItemParams(TypedDict, total=False):
    """Internal type for get item request."""

    reqType: str
    tableId: str
    params: Dict[str, Any]
    jwt: Optional[str]


class _ExecutePutItemParams(TypedDict, total=False):
    """Internal type for put item request."""

    reqType: str
    tableId: str
    params: Dict[str, Any]
    jwt: Optional[str]


class _ExecuteQueryItemParams(TypedDict, total=False):
    """Internal type for query item request."""

    reqType: str
    tableId: str
    params: Any
    jwt: Optional[str]


class _ExecuteDeleteItemParams(TypedDict, total=False):
    """Internal type for delete item request."""

    reqType: str
    tableId: str
    params: Dict[str, Any]
    jwt: Optional[str]


# Public types


class DsGetParams(TypedDict):
    """Parameters for get operation."""

    table_id: str
    key: Any


class DsGetItemResult(TypedDict, total=False):
    """Result from get operation."""

    result: Optional[str]
    error: Optional[str]
    params: Optional[Dict[str, Any]]


class DsPutParams(TypedDict):
    """Parameters for put operation."""

    table_id: str
    item: Any


class DsPutItemResult(TypedDict, total=False):
    """Result from put operation."""

    result: Optional[str]
    error: Optional[str]
    params: Optional[Dict[str, Any]]


class DsQueryParams(TypedDict, total=False):
    """Parameters for advanced query operation."""

    table_id: str
    expression: str
    start_key: Optional[str]
    values: Any
    limit: Optional[int]
    order: Optional[Union[bool, str]]  # false=desc, true=asc (inverted from proxy API)


class DsQueryResultParams(TypedDict, total=False):
    """Params structure for query result."""

    Items: List[Any]
    LastEvaluatedKey: Optional[Any]
    Count: Optional[int]


class DsQueryItemResult(TypedDict, total=False):
    """Result from query operation."""

    result: Optional[str]
    error: Optional[str]
    params: Optional[DsQueryResultParams]


class DsDeleteParams(TypedDict):
    """Parameters for delete operation."""

    table_id: str
    key: Any


class DsDeleteItemResult(TypedDict, total=False):
    """Result from delete operation."""

    result: Optional[str]
    error: Optional[str]
    params: Optional[Dict[str, Any]]


__all__ = [
    "DatastoreConfig",
    "DsGetParams",
    "DsGetItemResult",
    "DsPutParams",
    "DsPutItemResult",
    "DsQueryParams",
    "DsQueryItemResult",
    "DsDeleteParams",
    "DsDeleteItemResult",
]
