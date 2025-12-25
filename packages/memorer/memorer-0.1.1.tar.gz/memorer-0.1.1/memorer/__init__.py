"""
Memoirer SDK

Python SDK for Memoirer - Intelligent Memory for AI Agents.

Example:
    >>> from memorer import Memorer
    >>>
    >>> client = Memorer(api_key="your-api-key")
    >>>
    >>> # Ingest documents
    >>> client.knowledge.ingest(["AI agents need memory to be intelligent."])
    >>>
    >>> # Query with multi-hop reasoning
    >>> result = client.knowledge.query("Why do AI agents need memory?")
    >>> print(result.answer)
    >>> print(f"Confidence: {result.confidence}")
    >>>
    >>> # List memories
    >>> memories = client.memories.list(limit=10)
    >>> for memory in memories.memories:
    ...     print(f"{memory.type}: {memory.content}")
    >>>
    >>> # Chat with streaming
    >>> for event in client.chat.send_message("Hello!", stream=True):
    ...     if event.type == "token":
    ...         print(event.content, end="")
"""

from memorer.client import AsyncMemorer, Memorer
from memorer.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    MemorerError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    StreamingError,
    ValidationError,
)
from memorer.types import (
    BulkDeleteResponse,
    Citation,
    Conversation,
    ConversationDetail,
    ConversationListResponse,
    DerivedMemory,
    DerivedMemoryListResponse,
    Document,
    DoneEvent,
    Entity,
    EntityListResponse,
    EntityRelationships,
    EntityUpdate,
    ErrorEvent,
    ExtractionConfig,
    GraphStats,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    Memory,
    MemoryListResponse,
    MemorySource,
    MemoryStats,
    Message,
    MetadataEvent,
    QueryRequest,
    QueryResponse,
    ReasoningChain,
    ReasoningStep,
    Relationship,
    RetrievalPath,
    Scope,
    SendMessageRequest,
    StreamEvent,
    TokenEvent,
)

__version__ = "0.1.0"

__all__ = [
    # Clients
    "Memorer",
    "AsyncMemorer",
    # Errors
    "MemorerError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "NetworkError",
    "StreamingError",
    # Enums
    "Scope",
    "MemorySource",
    "RetrievalPath",
    # Knowledge types
    "Document",
    "ExtractionConfig",
    "IngestRequest",
    "IngestResponse",
    "QueryRequest",
    "QueryResponse",
    "ReasoningStep",
    "ReasoningChain",
    "Citation",
    "GraphStats",
    # Entity types
    "Entity",
    "EntityUpdate",
    "EntityListResponse",
    "EntityRelationships",
    "Relationship",
    "BulkDeleteResponse",
    # Memory types
    "Memory",
    "DerivedMemory",
    "MemoryListResponse",
    "DerivedMemoryListResponse",
    "MemoryStats",
    # Chat types
    "Conversation",
    "ConversationDetail",
    "ConversationListResponse",
    "Message",
    "SendMessageRequest",
    # Streaming types
    "StreamEvent",
    "TokenEvent",
    "MetadataEvent",
    "DoneEvent",
    "ErrorEvent",
    # Health types
    "HealthResponse",
]
