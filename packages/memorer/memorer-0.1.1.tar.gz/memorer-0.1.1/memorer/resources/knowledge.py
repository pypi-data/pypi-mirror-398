"""
Memoirer SDK Knowledge Resource

Query, ingest, and graph statistics operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from memorer.types import (
    Community,
    CommunityDetectResponse,
    CommunityListResponse,
    Document,
    DuplicatePair,
    DuplicatesResponse,
    ExtractionConfig,
    GraphCommunity,
    GraphEdge,
    GraphNode,
    GraphStats,
    GraphStatsDetail,
    GraphVisualization,
    IngestResponse,
    MergeResponse,
    QueryResponse,
    Relationship,
    RelationshipListResponse,
    Scope,
)

if TYPE_CHECKING:
    from memorer._http import AsyncHTTPClient, HTTPClient


class KnowledgeResource:
    """Synchronous knowledge resource operations."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def query(
        self,
        query: str,
        *,
        category: str | None = None,
        max_hops: int = 3,
        confidence_threshold: float = 0.7,
        timeout_ms: int = 5000,
        return_reasoning_trace: bool = True,
    ) -> QueryResponse:
        """
        Query the knowledge graph with multi-hop reasoning.

        Args:
            query: The question to ask
            category: Optional category filter
            max_hops: Maximum reasoning hops (1-5)
            confidence_threshold: Minimum confidence threshold (0.0-1.0)
            timeout_ms: Query timeout in milliseconds
            return_reasoning_trace: Whether to return reasoning chains

        Returns:
            QueryResponse with answer, reasoning chains, and citations

        Example:
            >>> result = client.knowledge.query("What caused the 2008 crisis?")
            >>> print(result.answer)
            >>> for chain in result.reasoning_chains:
            ...     print(f"Confidence: {chain.total_confidence}")
        """
        data = {
            "query": query,
            "max_hops": max_hops,
            "confidence_threshold": confidence_threshold,
            "timeout_ms": timeout_ms,
            "return_reasoning_trace": return_reasoning_trace,
        }
        if category:
            data["category"] = category

        response = self._http.post("/v1/knowledge/query", json_data=data)
        return QueryResponse(**response)

    def ingest(
        self,
        documents: list[Document] | list[dict[str, Any]] | list[str],
        *,
        scope: Scope | str | None = None,
        extract_entities: bool = True,
        extract_relationships: bool = True,
        compute_pagerank: bool = False,
    ) -> IngestResponse:
        """
        Ingest documents into the knowledge graph.

        Args:
            documents: List of documents to ingest. Can be:
                - List of Document objects
                - List of dicts with 'content' and optional 'metadata'
                - List of strings (content only)
            scope: Memory scope (user, project, organization)
            extract_entities: Whether to extract entities
            extract_relationships: Whether to extract relationships
            compute_pagerank: Whether to compute PageRank after ingestion

        Returns:
            IngestResponse with creation statistics

        Example:
            >>> result = client.knowledge.ingest([
            ...     "AI agents need memory to be intelligent.",
            ...     {"content": "Memory enables context.", "metadata": {"source": "blog"}}
            ... ])
            >>> print(f"Created {result.entities_created} entities")
        """
        # Normalize documents to list of dicts
        normalized_docs = []
        for doc in documents:
            if isinstance(doc, str):
                normalized_docs.append({"content": doc})
            elif isinstance(doc, Document):
                normalized_docs.append(doc.model_dump(exclude_none=True))
            else:
                normalized_docs.append(doc)

        data: dict[str, Any] = {
            "documents": normalized_docs,
            "extraction_config": {
                "extract_entities": extract_entities,
                "extract_relationships": extract_relationships,
                "compute_pagerank": compute_pagerank,
            },
        }
        if scope:
            data["scope"] = scope if isinstance(scope, str) else scope.value

        response = self._http.post("/v1/knowledge/ingest", json_data=data)
        return IngestResponse(**response)

    def stats(self) -> GraphStats:
        """
        Get knowledge graph statistics.

        Returns:
            GraphStats with entity counts, relationship counts, etc.

        Example:
            >>> stats = client.knowledge.stats()
            >>> print(f"Total entities: {stats.total_entities}")
        """
        response = self._http.get("/v1/knowledge/stats")
        return GraphStats(**response)

    def relationships(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> RelationshipListResponse:
        """
        List relationships in the knowledge graph.

        Args:
            limit: Maximum number of relationships to return
            offset: Pagination offset

        Returns:
            RelationshipListResponse with count and relationships

        Example:
            >>> result = client.knowledge.relationships(limit=50)
            >>> for rel in result.relationships:
            ...     print(f"{rel.source_id} --{rel.relation_type}--> {rel.target_id}")
        """
        params: dict[str, int] = {"limit": limit, "offset": offset}
        response = self._http.get("/v1/knowledge/relationships", params=params)
        relationships = [Relationship(**r) for r in response.get("relationships", [])]
        return RelationshipListResponse(
            count=response.get("count", 0),
            relationships=relationships,
        )

    def graph(
        self,
        *,
        limit: int = 500,
        include_embeddings: bool = False,
    ) -> GraphVisualization:
        """
        Get the full knowledge graph for visualization.

        Returns nodes, edges, communities, and stats in a format
        compatible with D3.js, vis.js, Cytoscape, etc.

        Args:
            limit: Maximum number of nodes to return
            include_embeddings: Include embedding vectors (large!)

        Returns:
            GraphVisualization with nodes, edges, communities, and stats

        Example:
            >>> graph = client.knowledge.graph(limit=100)
            >>> print(f"Nodes: {graph.stats.total_nodes}")
            >>> print(f"Edges: {graph.stats.total_edges}")
        """
        params: dict[str, Any] = {"limit": limit, "include_embeddings": include_embeddings}
        response = self._http.get("/v1/knowledge/graph", params=params)

        nodes = [GraphNode(**n) for n in response.get("nodes", [])]
        edges = [GraphEdge(**e) for e in response.get("edges", [])]
        communities = [GraphCommunity(**c) for c in response.get("communities", [])]
        stats = GraphStatsDetail(**response.get("stats", {}))

        return GraphVisualization(
            nodes=nodes,
            edges=edges,
            communities=communities,
            stats=stats,
        )

    def communities(self, *, limit: int = 20) -> CommunityListResponse:
        """
        List detected communities in the knowledge graph.

        Args:
            limit: Maximum number of communities to return

        Returns:
            CommunityListResponse with count and communities

        Example:
            >>> result = client.knowledge.communities()
            >>> for comm in result.communities:
            ...     print(f"{comm.label}: {comm.entity_count} entities")
        """
        response = self._http.get("/v1/knowledge/communities", params={"limit": limit})
        communities = [Community(**c) for c in response.get("communities", [])]
        return CommunityListResponse(
            count=response.get("count", 0),
            communities=communities,
        )

    def detect_communities(self, *, resolution: float = 1.0) -> CommunityDetectResponse:
        """
        Run community detection on the knowledge graph.

        This is a background operation that groups related entities.

        Args:
            resolution: Resolution parameter for Louvain algorithm (higher = more communities)

        Returns:
            CommunityDetectResponse with status message

        Example:
            >>> result = client.knowledge.detect_communities()
            >>> print(result.message)
        """
        response = self._http.post(
            "/v1/knowledge/communities/detect",
            params={"resolution": resolution},
        )
        return CommunityDetectResponse(**response)

    def find_duplicates(
        self,
        *,
        threshold: float = 0.90,
        limit: int = 50,
    ) -> DuplicatesResponse:
        """
        Find potential duplicate entities based on semantic similarity.

        Args:
            threshold: Similarity threshold (0.0-1.0, higher = more strict)
            limit: Maximum number of duplicate pairs to return

        Returns:
            DuplicatesResponse with found duplicate pairs

        Example:
            >>> result = client.knowledge.find_duplicates(threshold=0.95)
            >>> for pair in result.duplicates:
            ...     print(f"Duplicate: {pair.entity1.content} <-> {pair.entity2.content}")
        """
        params = {"threshold": threshold, "limit": limit}
        response = self._http.get("/v1/knowledge/deduplication/find-duplicates", params=params)
        duplicates = [DuplicatePair(**d) for d in response.get("duplicates", [])]
        return DuplicatesResponse(
            count=response.get("count", 0),
            threshold=response.get("threshold", threshold),
            duplicates=duplicates,
        )

    def merge_duplicates(
        self,
        keep_entity_id: str,
        merge_entity_id: str,
    ) -> MergeResponse:
        """
        Merge two duplicate entities.

        Keeps one entity and soft-deletes the other.
        Relationships are redirected to the kept entity.

        Args:
            keep_entity_id: ID of entity to keep
            merge_entity_id: ID of entity to merge (will be deleted)

        Returns:
            MergeResponse with merge details

        Example:
            >>> result = client.knowledge.merge_duplicates(
            ...     keep_entity_id="uuid-to-keep",
            ...     merge_entity_id="uuid-to-merge"
            ... )
            >>> print(f"Redirected {result.relationships_redirected} relationships")
        """
        response = self._http.post(
            "/v1/knowledge/deduplication/merge",
            json_data={
                "keep_entity_id": keep_entity_id,
                "merge_entity_id": merge_entity_id,
            },
        )
        return MergeResponse(**response)


class AsyncKnowledgeResource:
    """Asynchronous knowledge resource operations."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def query(
        self,
        query: str,
        *,
        category: str | None = None,
        max_hops: int = 3,
        confidence_threshold: float = 0.7,
        timeout_ms: int = 5000,
        return_reasoning_trace: bool = True,
    ) -> QueryResponse:
        """
        Query the knowledge graph with multi-hop reasoning.

        Args:
            query: The question to ask
            category: Optional category filter
            max_hops: Maximum reasoning hops (1-5)
            confidence_threshold: Minimum confidence threshold (0.0-1.0)
            timeout_ms: Query timeout in milliseconds
            return_reasoning_trace: Whether to return reasoning chains

        Returns:
            QueryResponse with answer, reasoning chains, and citations
        """
        data = {
            "query": query,
            "max_hops": max_hops,
            "confidence_threshold": confidence_threshold,
            "timeout_ms": timeout_ms,
            "return_reasoning_trace": return_reasoning_trace,
        }
        if category:
            data["category"] = category

        response = await self._http.post("/v1/knowledge/query", json_data=data)
        return QueryResponse(**response)

    async def ingest(
        self,
        documents: list[Document] | list[dict[str, Any]] | list[str],
        *,
        scope: Scope | str | None = None,
        extract_entities: bool = True,
        extract_relationships: bool = True,
        compute_pagerank: bool = False,
    ) -> IngestResponse:
        """
        Ingest documents into the knowledge graph.

        Args:
            documents: List of documents to ingest
            scope: Memory scope (user, project, organization)
            extract_entities: Whether to extract entities
            extract_relationships: Whether to extract relationships
            compute_pagerank: Whether to compute PageRank after ingestion

        Returns:
            IngestResponse with creation statistics
        """
        # Normalize documents to list of dicts
        normalized_docs = []
        for doc in documents:
            if isinstance(doc, str):
                normalized_docs.append({"content": doc})
            elif isinstance(doc, Document):
                normalized_docs.append(doc.model_dump(exclude_none=True))
            else:
                normalized_docs.append(doc)

        data: dict[str, Any] = {
            "documents": normalized_docs,
            "extraction_config": {
                "extract_entities": extract_entities,
                "extract_relationships": extract_relationships,
                "compute_pagerank": compute_pagerank,
            },
        }
        if scope:
            data["scope"] = scope if isinstance(scope, str) else scope.value

        response = await self._http.post("/v1/knowledge/ingest", json_data=data)
        return IngestResponse(**response)

    async def stats(self) -> GraphStats:
        """
        Get knowledge graph statistics.

        Returns:
            GraphStats with entity counts, relationship counts, etc.
        """
        response = await self._http.get("/v1/knowledge/stats")
        return GraphStats(**response)

    async def relationships(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> RelationshipListResponse:
        """
        List relationships in the knowledge graph.

        Args:
            limit: Maximum number of relationships to return
            offset: Pagination offset

        Returns:
            RelationshipListResponse with count and relationships
        """
        params: dict[str, int] = {"limit": limit, "offset": offset}
        response = await self._http.get("/v1/knowledge/relationships", params=params)
        relationships = [Relationship(**r) for r in response.get("relationships", [])]
        return RelationshipListResponse(
            count=response.get("count", 0),
            relationships=relationships,
        )

    async def graph(
        self,
        *,
        limit: int = 500,
        include_embeddings: bool = False,
    ) -> GraphVisualization:
        """
        Get the full knowledge graph for visualization.

        Args:
            limit: Maximum number of nodes to return
            include_embeddings: Include embedding vectors (large!)

        Returns:
            GraphVisualization with nodes, edges, communities, and stats
        """
        params: dict[str, Any] = {"limit": limit, "include_embeddings": include_embeddings}
        response = await self._http.get("/v1/knowledge/graph", params=params)

        nodes = [GraphNode(**n) for n in response.get("nodes", [])]
        edges = [GraphEdge(**e) for e in response.get("edges", [])]
        communities = [GraphCommunity(**c) for c in response.get("communities", [])]
        stats = GraphStatsDetail(**response.get("stats", {}))

        return GraphVisualization(
            nodes=nodes,
            edges=edges,
            communities=communities,
            stats=stats,
        )

    async def communities(self, *, limit: int = 20) -> CommunityListResponse:
        """
        List detected communities in the knowledge graph.

        Args:
            limit: Maximum number of communities to return

        Returns:
            CommunityListResponse with count and communities
        """
        response = await self._http.get("/v1/knowledge/communities", params={"limit": limit})
        communities = [Community(**c) for c in response.get("communities", [])]
        return CommunityListResponse(
            count=response.get("count", 0),
            communities=communities,
        )

    async def detect_communities(self, *, resolution: float = 1.0) -> CommunityDetectResponse:
        """
        Run community detection on the knowledge graph.

        Args:
            resolution: Resolution parameter for Louvain algorithm

        Returns:
            CommunityDetectResponse with status message
        """
        response = await self._http.post(
            "/v1/knowledge/communities/detect",
            params={"resolution": resolution},
        )
        return CommunityDetectResponse(**response)

    async def find_duplicates(
        self,
        *,
        threshold: float = 0.90,
        limit: int = 50,
    ) -> DuplicatesResponse:
        """
        Find potential duplicate entities based on semantic similarity.

        Args:
            threshold: Similarity threshold (0.0-1.0)
            limit: Maximum number of duplicate pairs to return

        Returns:
            DuplicatesResponse with found duplicate pairs
        """
        params = {"threshold": threshold, "limit": limit}
        response = await self._http.get("/v1/knowledge/deduplication/find-duplicates", params=params)
        duplicates = [DuplicatePair(**d) for d in response.get("duplicates", [])]
        return DuplicatesResponse(
            count=response.get("count", 0),
            threshold=response.get("threshold", threshold),
            duplicates=duplicates,
        )

    async def merge_duplicates(
        self,
        keep_entity_id: str,
        merge_entity_id: str,
    ) -> MergeResponse:
        """
        Merge two duplicate entities.

        Args:
            keep_entity_id: ID of entity to keep
            merge_entity_id: ID of entity to merge (will be deleted)

        Returns:
            MergeResponse with merge details
        """
        response = await self._http.post(
            "/v1/knowledge/deduplication/merge",
            json_data={
                "keep_entity_id": keep_entity_id,
                "merge_entity_id": merge_entity_id,
            },
        )
        return MergeResponse(**response)
