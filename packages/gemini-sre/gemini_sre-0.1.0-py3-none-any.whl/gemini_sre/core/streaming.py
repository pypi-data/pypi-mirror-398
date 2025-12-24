"""
Streaming response handler with retry logic.

Handles streaming responses with automatic reconnection on failure.
"""

from collections.abc import Iterator
from typing import Any, Callable, Optional


class StreamingHandler:
    """
    Handle streaming responses with retry logic.

    Automatically reconnects and retries streaming operations on failure.
    """

    def __init__(
        self,
        sre_client: Any,  # GeminiSREClient
        operation_func: Callable,
        operation_type: str,
        request_id: Optional[str],
    ):
        """
        Initialize streaming handler.

        Args:
            sre_client: Parent GeminiSREClient instance
            operation_func: Function that returns streaming iterator
            operation_type: Type of operation for retry config
            request_id: Optional request ID for tracking
        """
        self._sre_client = sre_client
        self._operation_func = operation_func
        self._operation_type = operation_type
        self._request_id = request_id
        self._retry_config = sre_client._retry_config.get_config(operation_type)

    def __iter__(self) -> Iterator[Any]:
        """
        Iterate over streaming response with retry.

        Automatically reconnects on failure and continues streaming.
        """
        max_retries = self._retry_config["max_retries"]

        for attempt in range(max_retries + 1):
            try:
                # Get stream from operation
                stream = self._sre_client._execute_with_failover(
                    operation_func=self._operation_func,
                    operation_type=self._operation_type,
                    request_id=self._request_id,
                )

                # Yield chunks
                yield from stream

                # Success - exit
                return

            except Exception as e:
                if attempt >= max_retries:
                    # Max retries exhausted
                    raise

                # Log and retry
                self._sre_client._logger.warning(
                    f"Stream failed (attempt {attempt + 1}/{max_retries}): {e}"
                )

                # Calculate backoff
                delay = self._sre_client._calculate_backoff(attempt, self._retry_config)
                import time

                time.sleep(delay)

    # TODO: Implement async version for aio namespace
    # async def __aiter__(self):
    #     """Async iterator for streaming responses."""
    #     pass
