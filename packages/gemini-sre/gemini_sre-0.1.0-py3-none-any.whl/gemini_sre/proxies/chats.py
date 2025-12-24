"""
Chats namespace proxy.

Wraps client.chats.* methods with SRE features for stateful operations.
"""

from typing import Optional


class ChatsProxy:
    """Proxy for client.chats namespace."""

    def __init__(self, sre_client):
        """Initialize chats proxy."""
        self._sre_client = sre_client

    def create(self, model: str, config=None, *, request_id: Optional[str] = None, **kwargs):
        """
        Create chat session.

        Returns a ChatProxy that wraps the SDK Chat object with SRE features.

        Args:
            model: Model name (e.g., "gemini-2.5-flash")
            config: Optional chat configuration
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Returns:
            ChatProxy wrapping the SDK chat session
        """

        def _operation(client, location):
            return client.chats.create(
                model=model,
                config=config,
                **kwargs,
            )

        # Create chat session (stateful operation, limited retry)
        sdk_chat = self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="stateful",
            request_id=request_id,
        )

        # Wrap in ChatProxy for SRE features on messages
        return ChatProxy(
            sre_client=self._sre_client,
            sdk_chat=sdk_chat,
            model=model,
            config=config,
        )


class ChatProxy:
    """Proxy for Chat objects (stateful)."""

    def __init__(self, sre_client, sdk_chat, model: str, config):
        """Initialize chat proxy."""
        self._sre_client = sre_client
        self._sdk_chat = sdk_chat
        self._model = model
        self._config = config

    def send_message(
        self, contents: str, config=None, *, request_id: Optional[str] = None, **kwargs
    ):
        """
        Send message with SRE features.

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
        response = self._sdk_chat.send_message(
            message=contents,
            config=config,
            **kwargs,
        )

        return response

    def send_message_stream(
        self, contents: str, config=None, *, request_id: Optional[str] = None, **kwargs
    ):
        """
        Send message with streaming response.

        Args:
            contents: Message content
            config: Optional message configuration
            request_id: Optional request ID for tracking
            **kwargs: Additional parameters

        Returns:
            Streaming iterator of response chunks
        """
        # Streaming chat (stateful streaming)
        # SDK expects 'message' parameter
        stream = self._sdk_chat.send_message_stream(
            message=contents,
            config=config,
            **kwargs,
        )

        return stream

    def get_history(self):
        """Get conversation history (local operation, no SRE needed)."""
        return self._sdk_chat.get_history()
