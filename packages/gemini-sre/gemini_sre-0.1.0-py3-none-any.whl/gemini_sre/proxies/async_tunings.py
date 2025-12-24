"""
Async Tunings namespace proxy.

Wraps client.aio.tunings.* methods with SRE features for async operations.
"""

from typing import Optional


class AsyncTuningsProxy:
    """Async proxy for client.aio.tunings namespace."""

    def __init__(self, sre_client):
        """Initialize async tunings proxy."""
        self._sre_client = sre_client

    async def create(
        self,
        *,
        request_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Create tuning job asynchronously with SRE features.

        Args:
            request_id: Optional request ID for tracking
            **kwargs: Tuning job parameters

        Returns:
            Created tuning job
        """

        async def _operation(client, location):
            return await client.aio.tunings.create(**kwargs)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="non_idempotent_write",
            request_id=request_id,
        )

    async def get(
        self,
        tuning_job: str,
        *,
        request_id: Optional[str] = None,
    ):
        """
        Get tuning job information asynchronously.

        Args:
            tuning_job: Tuning job name or ID
            request_id: Optional request ID for tracking

        Returns:
            Tuning job information
        """

        async def _operation(client, location):
            return await client.aio.tunings.get(tuning_job=tuning_job)

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
        List tuning jobs asynchronously.

        Args:
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Returns:
            List of tuning jobs
        """

        async def _operation(client, location):
            return await client.aio.tunings.list(**kwargs)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    async def delete(
        self,
        tuning_job: str,
        *,
        request_id: Optional[str] = None,
    ):
        """
        Delete tuning job asynchronously with SRE features.

        Args:
            tuning_job: Tuning job name or ID
            request_id: Optional request ID for tracking

        Returns:
            Delete response
        """

        async def _operation(client, location):
            return await client.aio.tunings.delete(tuning_job=tuning_job)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_delete",
            request_id=request_id,
        )
