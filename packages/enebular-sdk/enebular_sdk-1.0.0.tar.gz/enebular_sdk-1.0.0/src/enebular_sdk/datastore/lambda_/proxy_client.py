"""Internal utility class for building datastore proxy request payloads."""

from typing import Any, Dict

from ..constants import REQUEST_TYPE
from ..types import (
    DsDeleteParams,
    DsGetParams,
    DsPutParams,
    DsQueryParams,
    _ExecuteDeleteItemParams,
    _ExecuteGetItemParams,
    _ExecutePutItemParams,
    _ExecuteQueryItemParams,
)
from ...common import Logger


class ProxyClient:
    """Internal utility class for building datastore proxy request payloads."""

    _logger = Logger("ProxyClient")

    @staticmethod
    def get_item_request(params: DsGetParams) -> _ExecuteGetItemParams:
        """
        Build a get item request payload.

        Args:
            params: Get operation parameters

        Returns:
            Request payload for the proxy Lambda
        """
        ProxyClient._logger.trace("get_item_request", params)

        request: _ExecuteGetItemParams = {
            "reqType": REQUEST_TYPE.GET_ITEM,
            "tableId": params["table_id"],
            "params": {"Key": params["key"]},
        }

        ProxyClient._logger.trace_end("get_item_request", request)
        return request

    @staticmethod
    def put_item_request(params: DsPutParams) -> _ExecutePutItemParams:
        """
        Build a put item request payload.

        Args:
            params: Put operation parameters

        Returns:
            Request payload for the proxy Lambda
        """
        ProxyClient._logger.trace("put_item_request", params)

        request: _ExecutePutItemParams = {
            "reqType": REQUEST_TYPE.PUT_ITEM,
            "tableId": params["table_id"],
            "params": {"Item": params["item"]},
        }

        ProxyClient._logger.trace_end("put_item_request", request)
        return request

    @staticmethod
    def query_request(params: DsQueryParams) -> _ExecuteQueryItemParams:
        """
        Build a query request payload from custom expression parameters.

        Args:
            params: Query operation parameters

        Returns:
            Request payload for the proxy Lambda
        """
        ProxyClient._logger.trace("query_request", params)

        # Build query parameters
        query_params: Dict[str, Any] = {
            "QueryExpression": {
                "Expression": params.get("expression", ""),
                "Values": params.get("values", {}),
            }
        }

        # Limit
        limit = params.get("limit")
        if limit is not None:
            query_params["Limit"] = int(limit)
        else:
            query_params["Limit"] = 10  # Default limit

        # Order parameter handling
        # Proxy expects: Order=True for descending, Order=False for ascending
        # User API: order=False for descending, order=True for ascending (inverted!)
        # The inversion here converts user API (False=desc, True=asc) to proxy API (True=desc, False=asc)
        order_value = False  # Default: Order=False means ascending in proxy
        order = params.get("order")
        if order is not None:
            if isinstance(order, bool):
                order_value = not order
            elif isinstance(order, str):
                lower_str = order.lower()
                if lower_str == "true":
                    order_value = False
                elif lower_str == "false":
                    order_value = True
        query_params["Order"] = order_value

        # Pagination
        start_key = params.get("start_key")
        if start_key:
            query_params["StartKey"] = start_key

        request: _ExecuteQueryItemParams = {
            "reqType": REQUEST_TYPE.QUERY,
            "tableId": params["table_id"],
            "params": query_params,
        }

        ProxyClient._logger.trace_end("query_request", request)
        return request

    @staticmethod
    def delete_item_request(params: DsDeleteParams) -> _ExecuteDeleteItemParams:
        """
        Build a delete item request payload.

        Args:
            params: Delete operation parameters

        Returns:
            Request payload for the proxy Lambda
        """
        ProxyClient._logger.trace("delete_item_request", params)

        request: _ExecuteDeleteItemParams = {
            "reqType": REQUEST_TYPE.DELETE_ITEM,
            "tableId": params["table_id"],
            "params": {"Key": params["key"]},
        }

        ProxyClient._logger.trace_end("delete_item_request", request)
        return request
