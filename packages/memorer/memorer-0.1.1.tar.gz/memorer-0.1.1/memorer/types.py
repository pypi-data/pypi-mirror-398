"""
Memoirer SDK Types

Pydantic models for API requests and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================


class Scope(str, Enum):
    """Memory scope levels."""

    USER = "user"
    PROJECT = "project"
    ORGANIZATION = "organization"


class MemorySource(str, Enum):
    """Source of a memory."""

    DIRECT = "direct"
    DERIVED = "derived"
    INFERRED = "inferred"


class RetrievalPath(str, Enum):
    """Path used for retrieval."""

    CACHE = "cache"
    GRAPH = "graph"
    VECTOR = "vector"
    HYBRID = "hybrid"
    UNIFIED = "unified"


# ============================================================================
# Knowledge Types
# ============================================================================


class Document(BaseModel):
    """Document for ingestion."""

    content: str
    metadata: dict[str, Any] | None = None


class ExtractionConfig(BaseModel):
    """Configuration for entity/relationship extraction."""

    extract_entities: bool = True
    extract_relationships: bool = True
    compute_pagerank: bool = False


class IngestRequest(BaseModel):
    """Request to ingest documents."""

    documents: list[Document]
    scope: Scope | None = None
    extraction_config: ExtractionConfig = Field(default_factory=ExtractionConfig)


class IngestResponse(BaseModel):
    """Response from ingestion."""

    entities_created: int
    relationships_created: int
    episodes_created: int
    processing_time_ms: int
    status: Literal["success", "partial", "failed"]


class QueryRequest(BaseModel):
    """Request to query the knowledge graph."""

    query: str
    category: str | None = None
    max_hops: int = Field(default=3, ge=1, le=5)
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    timeout_ms: int = Field(default=5000, ge=10, le=30000)
    return_reasoning_trace: bool = True


class ReasoningStep(BaseModel):
    """A single step in a reasoning chain."""

    source_entity_id: str | None = None
    source_content: str | None = None
    relation_type: str | None = None
    target_entity_id: str | None = None
    target_content: str | None = None
    confidence: float = 0.0


class ReasoningChain(BaseModel):
    """A complete reasoning chain."""

    steps: list[ReasoningStep] = Field(default_factory=list)
    total_confidence: float = 0.0
    path_length: int = 0
    pagerank_score: float | None = None


class Citation(BaseModel):
    """Citation for a query response."""

    entity_id: str | None = None
    content: str | None = None
    doc_id: str | None = None
    title: str | None = None
    relevance: float = 0.0


class QueryResponse(BaseModel):
    """Response from a knowledge query."""

    answer: str
    reasoning_chains: list[ReasoningChain] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    confidence: float
    latency_ms: int
    path_used: str
    entities_found: int = 0


class GraphStats(BaseModel):
    """Knowledge graph statistics."""

    total_entities: int
    total_relationships: int
    total_episodes: int
    total_communities: int
    cache_size: int
    avg_importance: float


# ============================================================================
# Entity Types
# ============================================================================


class Entity(BaseModel):
    """An entity in the knowledge graph."""

    id: str
    type: str
    category: str | None = None
    content: str
    importance: float
    source: str
    scope: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EntityUpdate(BaseModel):
    """Request to update an entity."""

    content: str | None = None
    type: str | None = None
    category: str | None = None
    importance: float | None = None


class EntityListResponse(BaseModel):
    """Response with list of entities."""

    count: int
    entities: list[Entity]


class Relationship(BaseModel):
    """A relationship between entities."""

    id: str
    source_id: str
    target_id: str
    relation_type: str
    confidence: float


class EntityRelationships(BaseModel):
    """All relationships for an entity."""

    entity_id: str
    outgoing: list[Relationship]
    incoming: list[Relationship]


class BulkDeleteResponse(BaseModel):
    """Response from bulk delete operation."""

    deleted: int
    not_found: list[str]


# ============================================================================
# Memory Types
# ============================================================================


class Memory(BaseModel):
    """A memory item."""

    id: str
    content: str
    type: str
    category: str | None = None
    importance: float
    source: str
    created_at: datetime | None = None


class DerivedMemory(Memory):
    """A derived memory with source information."""

    derived_from: list[str] = Field(default_factory=list)
    derived_from_contents: list[str] = Field(default_factory=list)
    derivation_reason: str | None = None


class MemoryListResponse(BaseModel):
    """Response with list of memories."""

    count: int
    memories: list[Memory]


class DerivedMemoryListResponse(BaseModel):
    """Response with list of derived memories."""

    count: int
    memories: list[DerivedMemory]


class MemoryStats(BaseModel):
    """Memory statistics."""

    total_memories: int
    direct_memories: int
    derived_memories: int
    relationships: int


# ============================================================================
# Chat Types
# ============================================================================


class CreateConversationRequest(BaseModel):
    """Request to create a conversation."""

    model: str | None = None


class Conversation(BaseModel):
    """A conversation."""

    id: str
    model: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class Message(BaseModel):
    """A message in a conversation."""

    id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    reasoning_chains: list[dict[str, Any]] | None = None
    citations: list[dict[str, Any]] | None = None
    confidence: float | None = None
    latency_ms: int | None = None
    entities_found: int | None = None
    path_used: str | None = None
    created_at: datetime


class ConversationDetail(Conversation):
    """A conversation with its messages."""

    messages: list[Message]


class ConversationListResponse(BaseModel):
    """Response with list of conversations."""

    conversations: list[Conversation]
    total: int


class SendMessageRequest(BaseModel):
    """Request to send a message."""

    message: str
    conversation_id: str | None = None
    model: str | None = None
    max_context_messages: int = Field(default=10, ge=1, le=50)
    max_memory_hops: int = Field(default=3, ge=1, le=5)


# ============================================================================
# Streaming Types
# ============================================================================


class TokenEvent(BaseModel):
    """Token streaming event."""

    type: Literal["token"] = "token"
    content: str


class MetadataEvent(BaseModel):
    """Metadata streaming event."""

    type: Literal["metadata"] = "metadata"
    message_id: str
    conversation_id: str
    reasoning_chains: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float
    latency_ms: int
    entities_found: int
    path_used: str


class DoneEvent(BaseModel):
    """Done streaming event."""

    type: Literal["done"] = "done"
    status: Literal["complete"] = "complete"


class ErrorEvent(BaseModel):
    """Error streaming event."""

    type: Literal["error"] = "error"
    error: str


StreamEvent = TokenEvent | MetadataEvent | DoneEvent | ErrorEvent


# ============================================================================
# Health Types
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    database: Literal["connected", "disconnected"]


# ============================================================================
# Relationship Types
# ============================================================================


class RelationshipListResponse(BaseModel):
    """Response with list of relationships."""

    count: int
    relationships: list[Relationship]


# ============================================================================
# Graph Visualization Types
# ============================================================================


class GraphNode(BaseModel):
    """A node in the graph visualization."""

    id: str
    label: str
    title: str | None = None
    type: str
    category: str | None = None
    importance: float = 0.5
    pagerank: float = 0.0
    source: str | None = None
    scope: str | None = None
    emotional_valence: float | None = None
    emotional_intensity: float | None = None
    community: str | None = None
    created_at: datetime | None = None
    size: float = 10.0
    group: str | None = None
    embedding: list[float] | None = None


class GraphEdge(BaseModel):
    """An edge in the graph visualization."""

    id: str
    source: str  # D3.js format
    target: str
    label: str
    type: str
    confidence: float = 1.0
    width: float = 1.0
    arrows: str = "to"


class GraphCommunity(BaseModel):
    """A community in the graph."""

    id: str
    label: str | None = None
    summary: str | None = None
    entity_count: int = 0
    entity_ids: list[str] = Field(default_factory=list)


class GraphStatsDetail(BaseModel):
    """Detailed graph statistics."""

    total_nodes: int
    total_edges: int
    total_communities: int
    node_types: dict[str, int] = Field(default_factory=dict)
    edge_types: dict[str, int] = Field(default_factory=dict)
    avg_importance: float = 0.0
    avg_connections: float = 0.0


class GraphVisualization(BaseModel):
    """Full graph data for visualization."""

    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    communities: list[GraphCommunity] = Field(default_factory=list)
    stats: GraphStatsDetail


# ============================================================================
# Community Types
# ============================================================================


class Community(BaseModel):
    """A detected community."""

    id: str
    label: str | None = None
    summary: str | None = None
    entity_count: int = 0
    created_at: datetime | None = None


class CommunityListResponse(BaseModel):
    """Response with list of communities."""

    count: int
    communities: list[Community]


class CommunityDetectResponse(BaseModel):
    """Response from community detection."""

    status: str
    message: str


# ============================================================================
# Deduplication Types
# ============================================================================


class DuplicateEntity(BaseModel):
    """An entity in a duplicate pair."""

    id: str
    content: str
    type: str


class DuplicatePair(BaseModel):
    """A pair of duplicate entities."""

    entity1: DuplicateEntity
    entity2: DuplicateEntity


class DuplicatesResponse(BaseModel):
    """Response with found duplicates."""

    count: int
    threshold: float
    duplicates: list[DuplicatePair]


class MergeResponse(BaseModel):
    """Response from merging duplicates."""

    kept_entity_id: str
    merged_entity_id: str
    relationships_redirected: int


# ============================================================================
# Episode Types
# ============================================================================


class Episode(BaseModel):
    """A temporal episode grouping memories."""

    id: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    summary: str | None = None
    entity_count: int = 0
    created_at: datetime | None = None


class EpisodeListResponse(BaseModel):
    """Response with list of episodes."""

    count: int
    episodes: list[Episode]


class CreateEpisodeResponse(BaseModel):
    """Response from creating episodes."""

    created: int
    episodes: list[Episode]


# ============================================================================
# Consolidation Types
# ============================================================================


class ConsolidationResponse(BaseModel):
    """Response from memory consolidation (adaptive forgetting)."""

    status: str
    dry_run: bool
    entities_evaluated: int
    entities_soft_deleted: int
    entities_hard_deleted: int
    memory_reduction_pct: float
