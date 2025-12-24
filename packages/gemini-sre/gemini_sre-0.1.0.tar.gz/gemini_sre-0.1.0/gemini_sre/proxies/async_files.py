"""
Async Files namespace proxy.

Wraps client.aio.files.* methods with SRE features for async operations.
"""

from typing import Optional


class AsyncFilesProxy:
    """Async proxy for client.aio.files namespace."""

    def __init__(self, sre_client):
        """Initialize async files proxy."""
        self._sre_client = sre_client

    async def upload(
        self,
        file: str,
        *,
        config=None,
        request_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Upload file asynchronously with SRE features.

        Args:
            file: Path to file to upload
            config: Optional upload configuration
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Returns:
            Uploaded file information
        """

        async def _operation(client, location):
            return await client.aio.files.upload(
                file=file,
                config=config,
                **kwargs,
            )

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="non_idempotent_write",  # Upload creates new resource
            request_id=request_id,
        )

    async def get(
        self,
        file: str,
        *,
        request_id: Optional[str] = None,
    ):
        """
        Get file metadata asynchronously.

        Args:
            file: File name or resource name
            request_id: Optional request ID for tracking

        Returns:
            File metadata
        """

        async def _operation(client, location):
            return await client.aio.files.get(file=file)

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
        List uploaded files asynchronously.

        Args:
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters (page_size, page_token)

        Returns:
            List of uploaded files
        """

        async def _operation(client, location):
            return await client.aio.files.list(**kwargs)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    async def delete(
        self,
        file: str,
        *,
        request_id: Optional[str] = None,
    ):
        """
        Delete file asynchronously with SRE features.

        Args:
            file: File name or resource name
            request_id: Optional request ID for tracking

        Returns:
            Delete response
        """

        async def _operation(client, location):
            return await client.aio.files.delete(file=file)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_delete",
            request_id=request_id,
        )

    async def download(
        self,
        file: str,
        path: Optional[str] = None,
        *,
        request_id: Optional[str] = None,
    ):
        """
        Download file asynchronously with SRE features.

        Args:
            file: File name or resource name
            path: Local path to save file (optional)
            request_id: Optional request ID for tracking

        Returns:
            Downloaded file data
        """

        async def _operation(client, location):
            return await client.aio.files.download(file=file, path=path)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )
