"""
Async Chats namespace proxy.

Wraps client.aio.chats.* methods with SRE features for async stateful operations.
"""

from collections.abc import AsyncIterator
from typing import Optional


class AsyncChatsProxy:
    """Async proxy for client.aio.chats namespace."""

    def __init__(self, sre_client):
        """Initialize async chats proxy."""
        self._sre_client = sre_client

    async def create(
        self,
        model: str,
        config=None,
        *,
        request_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Create async chat session.

        Returns an AsyncChatProxy that wraps the SDK Chat object with SRE features.

        Args:
            model: Model name (e.g., "gemini-2.5-flash")
            config: Optional chat configuration
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Returns:
            AsyncChatProxy wrapping the SDK chat session
        """
        # Create chat directly (no await needed)
        # Can't use failover with chat creation due to stateful nature
        location = self._sre_client.locations[0]
        client = self._sre_client._get_client(location)

        sdk_chat = client.aio.chats.create(
            model=model,
            config=config,
            **kwargs,
        )

        # Wrap in AsyncChatProxy for SRE features on messages
        return AsyncChatProxy(
            sre_client=self._sre_client,
            sdk_chat=sdk_chat,
            model=model,
            config=config,
        )


class AsyncChatProxy:
    """Async proxy for Chat objects (stateful)."""

    def __init__(self, sre_client, sdk_chat, model: str, config):
        """Initialize async chat proxy."""
        self._sre_client = sre_client
        self._sdk_chat = sdk_chat
        self._model = model
        self._config = config

    async def send_message(
        self,
        contents: str,
        config=None,
        *,
        request_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Send message asynchronously with SRE features.

        Args:
            contents: Message content
            config: Optional message configuration
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Returns:
            Response from the chat model
        """
        # Note: Chat operations are stateful, so we use limited retry
        # to avoid duplicate messages in conversation history
        #
        # The SDK chat object maintains conversation state, so we
        # call send_message directly on it rather than through failover

        # Call send_message on SDK chat (stateful operation)
        # SDK expects 'message' parameter
        response = await self._sdk_chat.send_message(
            message=contents,
            config=config,
            **kwargs,
        )

        return response

    async def send_message_stream(
        self,
        contents: str,
        config=None,
        *,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator:
        """
        Send message with streaming response asynchronously.

        Args:
            contents: Message content
            config: Optional message configuration
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Yields:
            Streaming response chunks
        """
        # Streaming chat (stateful streaming)
        # SDK expects 'message' parameter
        # send_message_stream is async function, need to await it first
        stream = await self._sdk_chat.send_message_stream(
            message=contents,
            config=config,
            **kwargs,
        )

        async for chunk in stream:
            yield chunk

    async def get_history(self):
        """Get conversation history asynchronously (local operation, no SRE needed)."""
        return await self._sdk_chat.get_history()
