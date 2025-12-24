"""
Async Models namespace proxy.

Wraps client.aio.models.* methods with SRE features for async operations.
"""

from collections.abc import AsyncIterator
from typing import Optional


class AsyncModelsProxy:
    """Async proxy for client.aio.models namespace."""

    def __init__(self, sre_client):
        """Initialize async models proxy."""
        self._sre_client = sre_client

    async def generate_content(
        self,
        model: str,
        contents: str,
        *,
        config=None,
        request_id: Optional[str] = None,
        extra_body: Optional[dict] = None,
        **kwargs,
    ):
        """
        Generate content asynchronously with SRE features.

        Args:
            model: Model name (e.g., "gemini-2.5-flash")
            contents: Input text/content
            config: Optional generation configuration
            request_id: Optional request ID for tracking
            extra_body: Optional dictionary of extra request body parameters.
            **kwargs: Additional parameters

        Returns:
            Response from the model
        """
        if extra_body and "http_options" not in kwargs:
            kwargs["http_options"] = {"extra_body": extra_body}

        async def _operation(client, location):
            return await client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
                **kwargs,
            )

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    async def generate_content_stream(
        self,
        model: str,
        contents: str,
        *,
        config=None,
        request_id: Optional[str] = None,
        extra_body: Optional[dict] = None,
        **kwargs,
    ) -> AsyncIterator:
        """
        Generate content with streaming response asynchronously.

        Args:
            model: Model name (e.g., "gemini-2.5-flash")
            contents: Input text/content
            config: Optional generation configuration
            request_id: Optional request ID for tracking
            extra_body: Optional dictionary of extra request body parameters.
            **kwargs: Additional parameters

        Yields:
            Response chunks from the model
        """
        if extra_body and "http_options" not in kwargs:
            kwargs["http_options"] = {"extra_body": extra_body}

        # For streaming, we need to get the client first, then call stream method
        # Can't use failover with streaming due to state
        location = self._sre_client.locations[0]
        client = self._sre_client._get_client(location)

        # Get async stream generator (await the coroutine first)
        stream = await client.aio.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config,
            **kwargs,
        )

        # Yield chunks from the stream
        async for chunk in stream:
            yield chunk

    async def count_tokens(
        self,
        model: str,
        contents: str,
        *,
        request_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Count tokens asynchronously with SRE features.

        Args:
            model: Model name
            contents: Input content to count tokens for
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Returns:
            Token count response
        """

        async def _operation(client, location):
            return await client.aio.models.count_tokens(
                model=model,
                contents=contents,
                **kwargs,
            )

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    async def embed_content(
        self,
        model: str,
        contents: str,
        *,
        config=None,
        request_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Generate embeddings asynchronously with SRE features.

        Args:
            model: Model name (e.g., "text-embedding-004")
            contents: Input text to embed
            config: Optional embedding configuration
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Returns:
            Embedding response
        """

        async def _operation(client, location):
            return await client.aio.models.embed_content(
                model=model,
                contents=contents,
                config=config,
                **kwargs,
            )

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    async def get(
        self,
        model: str,
        *,
        request_id: Optional[str] = None,
    ):
        """
        Get model information asynchronously.

        Args:
            model: Model name to get information for
            request_id: Optional request ID for tracking

        Returns:
            Model information
        """

        async def _operation(client, location):
            return await client.aio.models.get(model=model)

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
        List available models asynchronously.

        Args:
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Returns:
            List of available models
        """

        async def _operation(client, location):
            return await client.aio.models.list(**kwargs)

        return await self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )
