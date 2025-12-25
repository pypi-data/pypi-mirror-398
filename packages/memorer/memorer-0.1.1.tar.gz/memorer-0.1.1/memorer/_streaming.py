"""
Memoirer SDK Streaming

SSE (Server-Sent Events) parser for streaming responses.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, AsyncIterator, Iterator

from memorer.errors import StreamingError
from memorer.types import DoneEvent, ErrorEvent, MetadataEvent, StreamEvent, TokenEvent

if TYPE_CHECKING:
    pass


def parse_sse_event(event_type: str, event_data: str) -> StreamEvent | None:
    """
    Parse a single SSE event into a typed event object.

    Args:
        event_type: The event type (token, metadata, done, error)
        event_data: The JSON data string

    Returns:
        Parsed event object or None if invalid
    """
    if not event_data:
        return None

    try:
        data = json.loads(event_data)
    except json.JSONDecodeError:
        return None

    if event_type == "token":
        return TokenEvent(content=data.get("content", ""))
    elif event_type == "metadata":
        return MetadataEvent(
            message_id=data.get("message_id", ""),
            conversation_id=data.get("conversation_id", ""),
            reasoning_chains=data.get("reasoning_chains", []),
            citations=data.get("citations", []),
            confidence=data.get("confidence", 0.0),
            latency_ms=data.get("latency_ms", 0),
            entities_found=data.get("entities_found", 0),
            path_used=data.get("path_used", ""),
        )
    elif event_type == "done":
        return DoneEvent()
    elif event_type == "error":
        return ErrorEvent(error=data.get("error", "Unknown error"))

    return None


def parse_sse_stream(lines: Iterator[str]) -> Iterator[StreamEvent]:
    """
    Parse an SSE stream from raw lines.

    Args:
        lines: Iterator of raw SSE lines

    Yields:
        Parsed event objects
    """
    current_event = ""
    current_data = ""

    for line in lines:
        line = line.strip()

        if line.startswith("event:"):
            current_event = line[6:].strip()
        elif line.startswith("data:"):
            current_data = line[5:].strip()
        elif line == "" and current_event and current_data:
            # Empty line marks end of event
            event = parse_sse_event(current_event, current_data)
            if event is not None:
                yield event

                # Check for error event
                if isinstance(event, ErrorEvent):
                    raise StreamingError(event.error)

            current_event = ""
            current_data = ""


async def parse_sse_stream_async(lines: AsyncIterator[str]) -> AsyncIterator[StreamEvent]:
    """
    Parse an SSE stream from raw lines asynchronously.

    Args:
        lines: Async iterator of raw SSE lines

    Yields:
        Parsed event objects
    """
    current_event = ""
    current_data = ""

    async for line in lines:
        line = line.strip()

        if line.startswith("event:"):
            current_event = line[6:].strip()
        elif line.startswith("data:"):
            current_data = line[5:].strip()
        elif line == "" and current_event and current_data:
            # Empty line marks end of event
            event = parse_sse_event(current_event, current_data)
            if event is not None:
                yield event

                # Check for error event
                if isinstance(event, ErrorEvent):
                    raise StreamingError(event.error)

            current_event = ""
            current_data = ""


class StreamBuffer:
    """
    Buffer for accumulating streaming content and metadata.

    Useful for collecting the full response while streaming.
    """

    def __init__(self) -> None:
        self.content: str = ""
        self.metadata: MetadataEvent | None = None
        self._done: bool = False

    def process_event(self, event: StreamEvent) -> None:
        """Process a streaming event."""
        if isinstance(event, TokenEvent):
            self.content += event.content
        elif isinstance(event, MetadataEvent):
            self.metadata = event
        elif isinstance(event, DoneEvent):
            self._done = True

    @property
    def is_done(self) -> bool:
        return self._done
