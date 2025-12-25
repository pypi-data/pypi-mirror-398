"""
Memoirer SDK Chat Resource

Conversation and message operations with streaming support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterator, Callable, Iterator

from memorer._streaming import StreamBuffer, parse_sse_stream, parse_sse_stream_async
from memorer.types import (
    Conversation,
    ConversationDetail,
    ConversationListResponse,
    DoneEvent,
    Message,
    MetadataEvent,
    StreamEvent,
    TokenEvent,
)

if TYPE_CHECKING:
    from memorer._http import AsyncHTTPClient, HTTPClient


class ChatResponse:
    """
    Response from a chat message, either streamed or complete.

    When stream=False, contains the full response.
    When stream=True, use as an iterator to get events.
    """

    def __init__(
        self,
        *,
        content: str = "",
        metadata: MetadataEvent | None = None,
        events: list[StreamEvent] | None = None,
    ) -> None:
        self.content = content
        self.metadata = metadata
        self._events = events or []

    @property
    def message_id(self) -> str | None:
        return self.metadata.message_id if self.metadata else None

    @property
    def conversation_id(self) -> str | None:
        return self.metadata.conversation_id if self.metadata else None

    @property
    def confidence(self) -> float | None:
        return self.metadata.confidence if self.metadata else None

    @property
    def latency_ms(self) -> int | None:
        return self.metadata.latency_ms if self.metadata else None

    @property
    def reasoning_chains(self) -> list[dict]:
        return self.metadata.reasoning_chains if self.metadata else []


class ChatResource:
    """Synchronous chat operations."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create_conversation(
        self,
        *,
        model: str | None = None,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            model: Optional model to use (e.g., "anthropic/claude-3.5-haiku")

        Returns:
            Created Conversation object

        Example:
            >>> conv = client.chat.create_conversation()
            >>> print(conv.id)
        """
        data = {}
        if model:
            data["model"] = model

        response = self._http.post("/v1/chat/conversations", json_data=data)
        return Conversation(
            id=response["conversation_id"],
            model=response.get("model", ""),
            message_count=0,
            created_at=response["created_at"],
            updated_at=response["created_at"],
        )

    def list_conversations(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> ConversationListResponse:
        """
        List conversations.

        Args:
            skip: Number of conversations to skip
            limit: Maximum number to return

        Returns:
            ConversationListResponse with conversations and total count

        Example:
            >>> result = client.chat.list_conversations(limit=10)
            >>> for conv in result.conversations:
            ...     print(conv.id)
        """
        response = self._http.get(
            "/v1/chat/conversations",
            params={"skip": skip, "limit": limit},
        )

        conversations = [Conversation(**c) for c in response.get("conversations", [])]
        return ConversationListResponse(
            conversations=conversations,
            total=response.get("total", 0),
        )

    def get_conversation(self, conversation_id: str) -> ConversationDetail:
        """
        Get a conversation with its message history.

        Args:
            conversation_id: UUID of the conversation

        Returns:
            ConversationDetail with messages

        Raises:
            NotFoundError: If conversation doesn't exist

        Example:
            >>> conv = client.chat.get_conversation("uuid-here")
            >>> for msg in conv.messages:
            ...     print(f"{msg.role}: {msg.content}")
        """
        response = self._http.get(f"/v1/chat/conversations/{conversation_id}")

        messages = [Message(**m) for m in response.get("messages", [])]
        return ConversationDetail(
            id=response["id"],
            model=response["model"],
            message_count=response.get("message_count", 0),
            created_at=response["created_at"],
            updated_at=response["updated_at"],
            messages=messages,
        )

    def delete_conversation(self, conversation_id: str) -> None:
        """
        Delete a conversation.

        Args:
            conversation_id: UUID of the conversation

        Raises:
            NotFoundError: If conversation doesn't exist

        Example:
            >>> client.chat.delete_conversation("uuid-here")
        """
        self._http.delete(f"/v1/chat/conversations/{conversation_id}")

    def send_message(
        self,
        message: str,
        *,
        conversation_id: str | None = None,
        model: str | None = None,
        max_context_messages: int = 10,
        max_memory_hops: int = 3,
        stream: bool = False,
        on_token: Callable[[str], None] | None = None,
        on_metadata: Callable[[MetadataEvent], None] | None = None,
        on_done: Callable[[], None] | None = None,
    ) -> ChatResponse | Iterator[StreamEvent]:
        """
        Send a message and get a response.

        Args:
            message: The message to send
            conversation_id: Optional conversation ID (creates new if not provided)
            model: Optional model override
            max_context_messages: Number of previous messages to include
            max_memory_hops: Maximum reasoning hops for memory retrieval
            stream: If True, returns an iterator of streaming events
            on_token: Callback for each token (streaming only)
            on_metadata: Callback for metadata event (streaming only)
            on_done: Callback when done (streaming only)

        Returns:
            ChatResponse if stream=False, Iterator[StreamEvent] if stream=True

        Example (non-streaming):
            >>> response = client.chat.send_message("Hello!")
            >>> print(response.content)

        Example (streaming with iteration):
            >>> for event in client.chat.send_message("Hello!", stream=True):
            ...     if event.type == "token":
            ...         print(event.content, end="")

        Example (streaming with callbacks):
            >>> client.chat.send_message(
            ...     "Hello!",
            ...     stream=True,
            ...     on_token=lambda t: print(t, end=""),
            ...     on_done=lambda: print("\\nDone!")
            ... )
        """
        data = {
            "message": message,
            "max_context_messages": max_context_messages,
            "max_memory_hops": max_memory_hops,
        }
        if conversation_id:
            data["conversation_id"] = conversation_id
        if model:
            data["model"] = model

        # Determine endpoint
        if conversation_id:
            endpoint = f"/v1/chat/conversations/{conversation_id}/messages"
        else:
            endpoint = "/v1/chat/messages"

        if stream:
            # Return streaming iterator
            raw_lines = self._http.stream_post(endpoint, json_data=data)
            event_stream = parse_sse_stream(raw_lines)

            # If callbacks provided, consume stream with callbacks
            if on_token or on_metadata or on_done:
                buffer = StreamBuffer()
                for event in event_stream:
                    buffer.process_event(event)
                    if isinstance(event, TokenEvent) and on_token:
                        on_token(event.content)
                    elif isinstance(event, MetadataEvent) and on_metadata:
                        on_metadata(event)
                    elif isinstance(event, DoneEvent) and on_done:
                        on_done()

                return ChatResponse(content=buffer.content, metadata=buffer.metadata)

            return event_stream

        else:
            # Non-streaming: collect full response
            raw_lines = self._http.stream_post(endpoint, json_data=data)
            buffer = StreamBuffer()

            for event in parse_sse_stream(raw_lines):
                buffer.process_event(event)

            return ChatResponse(content=buffer.content, metadata=buffer.metadata)


class AsyncChatResource:
    """Asynchronous chat operations."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def create_conversation(
        self,
        *,
        model: str | None = None,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            model: Optional model to use

        Returns:
            Created Conversation object
        """
        data = {}
        if model:
            data["model"] = model

        response = await self._http.post("/v1/chat/conversations", json_data=data)
        return Conversation(
            id=response["conversation_id"],
            model=response.get("model", ""),
            message_count=0,
            created_at=response["created_at"],
            updated_at=response["created_at"],
        )

    async def list_conversations(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> ConversationListResponse:
        """
        List conversations.

        Args:
            skip: Number of conversations to skip
            limit: Maximum number to return

        Returns:
            ConversationListResponse with conversations and total count
        """
        response = await self._http.get(
            "/v1/chat/conversations",
            params={"skip": skip, "limit": limit},
        )

        conversations = [Conversation(**c) for c in response.get("conversations", [])]
        return ConversationListResponse(
            conversations=conversations,
            total=response.get("total", 0),
        )

    async def get_conversation(self, conversation_id: str) -> ConversationDetail:
        """
        Get a conversation with its message history.

        Args:
            conversation_id: UUID of the conversation

        Returns:
            ConversationDetail with messages
        """
        response = await self._http.get(f"/v1/chat/conversations/{conversation_id}")

        messages = [Message(**m) for m in response.get("messages", [])]
        return ConversationDetail(
            id=response["id"],
            model=response["model"],
            message_count=response.get("message_count", 0),
            created_at=response["created_at"],
            updated_at=response["updated_at"],
            messages=messages,
        )

    async def delete_conversation(self, conversation_id: str) -> None:
        """
        Delete a conversation.

        Args:
            conversation_id: UUID of the conversation
        """
        await self._http.delete(f"/v1/chat/conversations/{conversation_id}")

    async def send_message(
        self,
        message: str,
        *,
        conversation_id: str | None = None,
        model: str | None = None,
        max_context_messages: int = 10,
        max_memory_hops: int = 3,
        stream: bool = False,
        on_token: Callable[[str], None] | None = None,
        on_metadata: Callable[[MetadataEvent], None] | None = None,
        on_done: Callable[[], None] | None = None,
    ) -> ChatResponse | AsyncIterator[StreamEvent]:
        """
        Send a message and get a response.

        Args:
            message: The message to send
            conversation_id: Optional conversation ID (creates new if not provided)
            model: Optional model override
            max_context_messages: Number of previous messages to include
            max_memory_hops: Maximum reasoning hops for memory retrieval
            stream: If True, returns an async iterator of streaming events
            on_token: Callback for each token (streaming only)
            on_metadata: Callback for metadata event (streaming only)
            on_done: Callback when done (streaming only)

        Returns:
            ChatResponse if stream=False, AsyncIterator[StreamEvent] if stream=True

        Example (non-streaming):
            >>> response = await client.chat.send_message("Hello!")
            >>> print(response.content)

        Example (streaming):
            >>> async for event in await client.chat.send_message("Hello!", stream=True):
            ...     if event.type == "token":
            ...         print(event.content, end="")
        """
        data = {
            "message": message,
            "max_context_messages": max_context_messages,
            "max_memory_hops": max_memory_hops,
        }
        if conversation_id:
            data["conversation_id"] = conversation_id
        if model:
            data["model"] = model

        # Determine endpoint
        if conversation_id:
            endpoint = f"/v1/chat/conversations/{conversation_id}/messages"
        else:
            endpoint = "/v1/chat/messages"

        if stream:
            # Return streaming async iterator
            raw_lines = self._http.stream_post(endpoint, json_data=data)
            event_stream = parse_sse_stream_async(raw_lines)

            # If callbacks provided, consume stream with callbacks
            if on_token or on_metadata or on_done:
                buffer = StreamBuffer()
                async for event in event_stream:
                    buffer.process_event(event)
                    if isinstance(event, TokenEvent) and on_token:
                        on_token(event.content)
                    elif isinstance(event, MetadataEvent) and on_metadata:
                        on_metadata(event)
                    elif isinstance(event, DoneEvent) and on_done:
                        on_done()

                return ChatResponse(content=buffer.content, metadata=buffer.metadata)

            return event_stream

        else:
            # Non-streaming: collect full response
            raw_lines = self._http.stream_post(endpoint, json_data=data)
            buffer = StreamBuffer()

            async for event in parse_sse_stream_async(raw_lines):
                buffer.process_event(event)

            return ChatResponse(content=buffer.content, metadata=buffer.metadata)
