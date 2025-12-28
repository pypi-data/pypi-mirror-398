"""Main SDK entry point for Lambda functions to interact with Enebular datastore."""

import base64
import json
from typing import Any, Callable, Dict, Optional

import boto3
from botocore.exceptions import ClientError

from ..constants import ENEBULAR_DS_JWT, ENEBULAR_DS_PROXY_ARN
from ..exceptions import (
    DatastoreConfigError,
    DatastoreOperationError,
    ProxyInvocationError,
)
from ..types import (
    DatastoreConfig,
    DsDeleteParams,
    DsDeleteItemResult,
    DsGetItemResult,
    DsGetParams,
    DsPutItemResult,
    DsPutParams,
    DsQueryItemResult,
    DsQueryParams,
)
from .proxy_client import ProxyClient
from ...common import Logger


class CloudDataStoreClient:
    """
    Main SDK entry point for Lambda functions to interact with Enebular datastore.

    This client communicates with the Enebular datastore via a proxy Lambda function.
    It requires the following environment variables:
    - ENEBULAR_DS_JWT: JWT token for authentication
    - ENEBULAR_DS_PROXY_ARN: ARN of the proxy Lambda function

    Example:
        ```python
        from enebular_sdk import CloudDataStoreClient

        # Initialize client (reads from environment variables)
        client = CloudDataStoreClient()

        # Or provide configuration explicitly
        client = CloudDataStoreClient({
            'jwt': 'your-jwt-token',
            'proxy_arn': 'arn:aws:lambda:region:account:function:proxy'
        })

        # Use the client
        result = client.get_item({
            'table_id': 'my-table',
            'key': {'id': '123'}
        })
        ```
    """

    def __init__(self, config: Optional[DatastoreConfig] = None):
        """
        Initialize the CloudDataStoreClient.

        Args:
            config: Optional configuration. If not provided, reads from environment variables.

        Raises:
            DatastoreConfigError: If JWT or proxy ARN is not configured
        """
        self._logger = Logger("CloudDataStoreClient")
        self._logger.trace("constructor", config)

        # Get JWT from config or environment
        if config and config.get("jwt"):
            self._jwt = config["jwt"]
        else:
            self._jwt = ENEBULAR_DS_JWT

        if not self._jwt:
            raise DatastoreConfigError(
                "JWT is required. Set ENEBULAR_DS_JWT environment variable or provide jwt in config."
            )

        # Get proxy ARN from config or environment
        if config and config.get("proxy_arn"):
            self._proxy_arn = config["proxy_arn"]
        else:
            self._proxy_arn = ENEBULAR_DS_PROXY_ARN

        if not self._proxy_arn:
            raise DatastoreConfigError(
                "Proxy ARN is required. Set ENEBULAR_DS_PROXY_ARN environment variable or provide proxy_arn in config."
            )

        # Initialize AWS Lambda client
        self._lambda_client = boto3.client("lambda")

        self._logger.debug(
            "CloudDataStoreClient initialized",
            {"proxy_arn": self._proxy_arn, "has_jwt": bool(self._jwt)},
        )
        self._logger.trace_end("constructor")

    def _execute(self, request_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a request to the proxy Lambda function.

        Args:
            request_input: The request payload to send to the proxy

        Returns:
            The response from the proxy Lambda

        Raises:
            Exception: If the Lambda invocation fails or returns no payload
        """
        self._logger.trace("_execute", request_input)

        try:
            # Inject JWT into the request
            request_input["jwt"] = self._jwt

            # Invoke the proxy Lambda
            response = self._lambda_client.invoke(
                FunctionName=self._proxy_arn,
                InvocationType="RequestResponse",
                LogType="Tail",
                Payload=json.dumps(request_input),
            )

            # Decode logs if present
            if "LogResult" in response:
                log_result = base64.b64decode(response["LogResult"]).decode("utf-8")
                self._logger.debug("Lambda logs", {"logs": log_result})

            # Parse response payload
            if "Payload" not in response:
                raise ProxyInvocationError("No payload returned from proxy Lambda")

            payload_bytes = response["Payload"].read()
            result = json.loads(payload_bytes.decode("utf-8"))

            self._logger.trace_end("_execute", result)
            return result

        except ClientError as e:
            self._logger.error("Lambda invocation failed", e)
            raise ProxyInvocationError(f"Lambda invocation failed: {str(e)}") from e
        except Exception as e:
            self._logger.error("Execution failed", e)
            raise

    def _execute_operation(
        self,
        operation_name: str,
        request: Dict[str, Any],
        debug_info_fn: Optional[Callable[[Any], Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a datastore operation.

        Args:
            operation_name: Name of the operation for logging
            request: The request payload
            debug_info_fn: Optional function to extract debug info from the result

        Returns:
            The operation result

        Raises:
            DatastoreOperationError: If the operation fails
            ProxyInvocationError: If proxy invocation fails
        """
        self._logger.trace(operation_name, request)

        try:
            result = self._execute(request)

            # Check for errors in the response
            if result.get("error"):
                error_msg = result.get("error")
                self._logger.error(f"{operation_name} failed", error_msg)
                raise DatastoreOperationError(f"{operation_name} failed: {error_msg}")

            # Log debug info if available
            if debug_info_fn and result.get("params"):
                debug_info = debug_info_fn(result["params"])
                self._logger.debug(f"{operation_name} result", debug_info)

            self._logger.trace_end(operation_name, result)
            return result

        except Exception as e:
            self._logger.error(f"{operation_name} exception", e)
            raise

    def get_item(self, params: DsGetParams) -> DsGetItemResult:
        """
        Retrieve a single item by key.

        Args:
            params: Get operation parameters containing table_id and key

        Returns:
            Result containing the item if found

        Example:
            ```python
            result = client.get_item({
                'table_id': 'my-table',
                'key': {'user_id': 'user123', 'timestamp': 1234567890}
            })

            if result.get('result') == 'success':
                item = result['params']['Item']
                print(f"Retrieved item: {item}")
            ```
        """
        request = ProxyClient.get_item_request(params)

        def debug_info(result_params: Dict[str, Any]) -> Dict[str, Any]:
            return {"has_item": "Item" in result_params}

        return self._execute_operation("get_item", request, debug_info)  # type: ignore[arg-type, return-value]

    def put_item(self, params: DsPutParams) -> DsPutItemResult:
        """
        Store or update an item.

        Args:
            params: Put operation parameters containing table_id and item

        Returns:
            Result of the put operation

        Example:
            ```python
            result = client.put_item({
                'table_id': 'my-table',
                'item': {
                    'user_id': 'user123',
                    'timestamp': 1234567890,
                    'data': 'some data'
                }
            })

            if result.get('result') == 'success':
                print("Item stored successfully")
            ```
        """
        request = ProxyClient.put_item_request(params)
        return self._execute_operation("put_item", request)  # type: ignore[arg-type, return-value]

    def query(self, params: DsQueryParams) -> DsQueryItemResult:
        """
        Execute an advanced query with custom expressions.

        Args:
            params: Query parameters with custom expression

        Returns:
            Result containing matched items and pagination info

        Example:
            ```python
            result = client.query({
                'table_id': 'my-table',
                'expression': '#user_id = :user_id AND #timestamp > :timestamp',
                'values': {
                    ':user_id': 'user123',
                    ':timestamp': 1234567890
                },
                'limit': 20,
                'order': False  # descending (False=desc, True=asc in user API)
            })

            if result.get('result') == 'success':
                items = result['params']['Items']
                print(f"Found {len(items)} items")
            ```
        """
        request = ProxyClient.query_request(params)

        def debug_info(result_params: Dict[str, Any]) -> Dict[str, Any]:
            items = result_params.get("Items", [])
            return {
                "item_count": len(items),
                "has_more": "LastEvaluatedKey" in result_params,
            }

        return self._execute_operation("query", request, debug_info)  # type: ignore[arg-type, return-value]

    def delete_item(self, params: DsDeleteParams) -> DsDeleteItemResult:
        """
        Delete an item by key.

        Args:
            params: Delete operation parameters containing table_id and key

        Returns:
            Result of the delete operation

        Example:
            ```python
            result = client.delete_item({
                'table_id': 'my-table',
                'key': {'user_id': 'user123', 'timestamp': 1234567890}
            })

            if result.get('result') == 'success':
                print("Item deleted successfully")
            ```
        """
        request = ProxyClient.delete_item_request(params)
        return self._execute_operation("delete_item", request)  # type: ignore[arg-type, return-value]
