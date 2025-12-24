"""
Models namespace proxy.

Wraps client.models.* methods with SRE features.
"""

from typing import Any, Optional


class ModelsProxy:
    """Proxy for client.models namespace."""

    def __init__(self, sre_client):
        """
        Initialize models proxy.

        Args:
            sre_client: Parent GeminiSREClient instance
        """
        self._sre_client = sre_client

    def generate_content(
        self,
        model: str,
        contents: Any,
        config: Optional[Any] = None,
        *,
        request_id: Optional[str] = None,
        extra_body: Optional[dict] = None,
        **kwargs,
    ):
        """
        Generate content with SRE features.

        Wraps client.models.generate_content() with:
        - Automatic retry (idempotent operation)
        - Multi-region failover
        - Circuit breaker
        - Monitoring

        All parameters are passed through to the SDK method.

        Args:
            model: Model name (e.g., "gemini-2.5-flash")
            contents: Input prompt/conversation
            config: Optional GenerateContentConfig
            request_id: Optional request ID for tracking
            extra_body: Optional dictionary of extra request body parameters.
            **kwargs: Additional parameters

        Returns:
            GenerateContentResponse
        """
        if extra_body and "http_options" not in kwargs:
            kwargs["http_options"] = {"extra_body": extra_body}

        def _operation(client, location):
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
                **kwargs,
            )

        return self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    def generate_content_stream(
        self,
        model: str,
        contents: Any,
        config: Optional[Any] = None,
        *,
        request_id: Optional[str] = None,
        extra_body: Optional[dict] = None,
        **kwargs,
    ):
        """
        Generate content with streaming response.

        Wraps client.models.generate_content_stream() with:
        - Stream retry (reconnect on failure)
        - Circuit breaker
        - Monitoring

        Args:
            model: Model name
            contents: Input prompt/conversation
            config: Optional GenerateContentConfig
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Returns:
            StreamingHandler iterator
        """
        from gemini_sre.core.streaming import StreamingHandler

        def _operation(client, location):
            return client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
                **kwargs,
            )

        return StreamingHandler(
            sre_client=self._sre_client,
            operation_func=_operation,
            operation_type="streaming",
            request_id=request_id,
        )

    def count_tokens(
        self,
        model: str,
        contents: Any,
        *,
        request_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Count tokens with SRE features.

        Args:
            model: Model name
            contents: Input content
            request_id: Optional request ID
            **kwargs: Additional parameters

        Returns:
            CountTokensResponse
        """

        def _operation(client, location):
            return client.models.count_tokens(
                model=model,
                contents=contents,
                **kwargs,
            )

        return self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    def list(
        self,
        config: Optional[dict] = None,
        *,
        request_id: Optional[str] = None,
    ):
        """
        List models with SRE features.

        Args:
            config: Optional configuration dict
            request_id: Optional request ID

        Returns:
            Iterator or Pager of Model objects
        """

        def _operation(client, location):
            return client.models.list(config=config)

        return self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    def get(
        self,
        model: str,
        *,
        request_id: Optional[str] = None,
    ):
        """
        Get model details with SRE features.

        Args:
            model: Model name
            request_id: Optional request ID

        Returns:
            Model object
        """

        def _operation(client, location):
            return client.models.get(model=model)

        return self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    # TODO: Implement remaining methods
    # - generate_images()
    # - generate_videos()
    # - update()
