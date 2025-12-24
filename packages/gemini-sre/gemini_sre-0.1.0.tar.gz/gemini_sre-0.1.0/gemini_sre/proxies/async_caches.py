"""
Async Caches namespace proxy.

Wraps client.aio.caches.* methods with SRE features for async operations.
"""

from typing import Optional


class AsyncCachesProxy:
    """Async proxy for client.aio.caches namespace."""

    def __init__(self, sre_client):
        """Initialize async caches proxy."""
        self._sre_client = sre_client

    async def create(
        self,
        *,
        request_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Create cache asynchronously with SRE features.

        Args:
            request_id: Optional request ID for tracking
            **kwargs: Cache parameters

        Returns:
            Created cache
        """

        async def _operation(client, location):
            return await client.aio.caches.create(**kwargs)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="non_idempotent_write",
            request_id=request_id,
        )

    async def get(
        self,
        cache: str,
        *,
        request_id: Optional[str] = None,
    ):
        """
        Get cache information asynchronously.

        Args:
            cache: Cache name or ID
            request_id: Optional request ID for tracking

        Returns:
            Cache information
        """

        async def _operation(client, location):
            return await client.aio.caches.get(cache=cache)

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
        List caches asynchronously.

        Args:
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Returns:
            List of caches
        """

        async def _operation(client, location):
            return await client.aio.caches.list(**kwargs)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    async def delete(
        self,
        cache: str,
        *,
        request_id: Optional[str] = None,
    ):
        """
        Delete cache asynchronously with SRE features.

        Args:
            cache: Cache name or ID
            request_id: Optional request ID for tracking

        Returns:
            Delete response
        """

        async def _operation(client, location):
            return await client.aio.caches.delete(cache=cache)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_delete",
            request_id=request_id,
        )

    async def update(
        self,
        cache: str,
        *,
        request_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Update cache asynchronously with SRE features.

        Args:
            cache: Cache name or ID
            request_id: Optional request ID for tracking
            **kwargs: Update parameters

        Returns:
            Updated cache
        """

        async def _operation(client, location):
            return await client.aio.caches.update(cache=cache, **kwargs)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_update",
            request_id=request_id,
        )
