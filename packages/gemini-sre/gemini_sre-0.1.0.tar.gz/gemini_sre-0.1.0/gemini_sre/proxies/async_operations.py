"""
Async Operations namespace proxy.

Wraps client.aio.operations.* methods with SRE features for async operations.
"""

from typing import Optional


class AsyncOperationsProxy:
    """Async proxy for client.aio.operations namespace."""

    def __init__(self, sre_client):
        """Initialize async operations proxy."""
        self._sre_client = sre_client

    async def get(
        self,
        operation: str,
        *,
        request_id: Optional[str] = None,
    ):
        """
        Get operation status asynchronously.

        Args:
            operation: Operation name or ID
            request_id: Optional request ID for tracking

        Returns:
            Operation status
        """

        async def _operation(client, location):
            return await client.aio.operations.get(operation=operation)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    async def list(
        self,
        *,
        request_id: Optional[str] = None,
        **kwargs,
    ):
        """
        List operations asynchronously.

        Args:
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Returns:
            List of operations
        """

        async def _operation(client, location):
            return await client.aio.operations.list(**kwargs)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    async def cancel(
        self,
        operation: str,
        *,
        request_id: Optional[str] = None,
    ):
        """
        Cancel operation asynchronously with SRE features.

        Args:
            operation: Operation name or ID
            request_id: Optional request ID for tracking

        Returns:
            Cancel response
        """

        async def _operation(client, location):
            return await client.aio.operations.cancel(operation=operation)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_delete",
            request_id=request_id,
        )

    async def delete(
        self,
        operation: str,
        *,
        request_id: Optional[str] = None,
    ):
        """
        Delete operation asynchronously with SRE features.

        Args:
            operation: Operation name or ID
            request_id: Optional request ID for tracking

        Returns:
            Delete response
        """

        async def _operation(client, location):
            return await client.aio.operations.delete(operation=operation)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_delete",
            request_id=request_id,
        )
