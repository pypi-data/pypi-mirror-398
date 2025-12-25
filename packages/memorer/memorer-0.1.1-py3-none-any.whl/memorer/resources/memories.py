"""
Memoirer SDK Memories Resource

Memory management operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from memorer.types import (
    ConsolidationResponse,
    CreateEpisodeResponse,
    DerivedMemory,
    DerivedMemoryListResponse,
    Episode,
    EpisodeListResponse,
    Memory,
    MemoryListResponse,
    MemoryStats,
)

if TYPE_CHECKING:
    from memorer._http import AsyncHTTPClient, HTTPClient


class MemoriesResource:
    """Synchronous memory operations."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(
        self,
        *,
        limit: int = 50,
        category: str | None = None,
        type: str | None = None,
    ) -> MemoryListResponse:
        """
        List all memories.

        Args:
            limit: Maximum number of memories to return
            category: Filter by category (personal, work, etc.)
            type: Filter by type (fact, concept, etc.)

        Returns:
            MemoryListResponse with count and list of memories

        Example:
            >>> result = client.memories.list(limit=20)
            >>> for memory in result.memories:
            ...     print(f"{memory.type}: {memory.content}")
        """
        params: dict[str, str | int] = {"limit": limit}
        if category:
            params["category"] = category
        if type:
            params["type"] = type

        response = self._http.get("/v1/memories", params=params)

        memories = [Memory(**m) for m in response.get("memories", [])]
        return MemoryListResponse(count=response.get("count", 0), memories=memories)

    def list_direct(
        self,
        *,
        limit: int = 50,
        category: str | None = None,
    ) -> MemoryListResponse:
        """
        List direct memories (user-stated facts).

        Direct memories are high-confidence facts explicitly provided by the user.

        Args:
            limit: Maximum number of memories to return
            category: Filter by category

        Returns:
            MemoryListResponse with count and list of direct memories

        Example:
            >>> result = client.memories.list_direct()
            >>> for memory in result.memories:
            ...     print(memory.content)
        """
        params: dict[str, str | int] = {"limit": limit}
        if category:
            params["category"] = category

        response = self._http.get("/v1/memories/direct", params=params)

        memories = [Memory(**m) for m in response.get("memories", [])]
        return MemoryListResponse(count=response.get("count", 0), memories=memories)

    def list_derived(self, *, limit: int = 50) -> DerivedMemoryListResponse:
        """
        List derived memories (AI-synthesized insights).

        Derived memories are inferences made by combining multiple direct memories.

        Args:
            limit: Maximum number of memories to return

        Returns:
            DerivedMemoryListResponse with derivation information

        Example:
            >>> result = client.memories.list_derived()
            >>> for memory in result.memories:
            ...     print(f"Derived: {memory.content}")
            ...     print(f"From: {memory.derived_from_contents}")
        """
        response = self._http.get("/v1/memories/derived", params={"limit": limit})

        memories = [DerivedMemory(**m) for m in response.get("memories", [])]
        return DerivedMemoryListResponse(count=response.get("count", 0), memories=memories)

    def get(self, memory_id: str) -> Memory:
        """
        Get a specific memory by ID.

        Args:
            memory_id: UUID of the memory

        Returns:
            Memory object

        Raises:
            NotFoundError: If memory doesn't exist

        Example:
            >>> memory = client.memories.get("uuid-here")
            >>> print(memory.content)
        """
        response = self._http.get(f"/v1/memories/{memory_id}")

        # Check if it's a derived memory
        if response.get("derived_from"):
            return DerivedMemory(**response)
        return Memory(**response)

    def delete(self, memory_id: str) -> None:
        """
        Delete a memory (soft delete).

        Args:
            memory_id: UUID of the memory

        Raises:
            NotFoundError: If memory doesn't exist

        Example:
            >>> client.memories.delete("uuid-here")
        """
        self._http.delete(f"/v1/memories/{memory_id}")

    def stats(self) -> MemoryStats:
        """
        Get memory statistics.

        Returns:
            MemoryStats with memory counts

        Example:
            >>> stats = client.memories.stats()
            >>> print(f"Total: {stats.total_memories}")
            >>> print(f"Direct: {stats.direct_memories}")
            >>> print(f"Derived: {stats.derived_memories}")
        """
        response = self._http.get("/v1/memories/stats/summary")
        return MemoryStats(**response)

    def episodes(
        self,
        *,
        limit: int = 20,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> EpisodeListResponse:
        """
        List temporal episodes (time-windowed memory groups).

        Args:
            limit: Maximum number of episodes to return
            start_time: Filter by start time (ISO format)
            end_time: Filter by end time (ISO format)

        Returns:
            EpisodeListResponse with count and episodes

        Example:
            >>> result = client.memories.episodes(limit=10)
            >>> for episode in result.episodes:
            ...     print(f"{episode.summary}: {episode.entity_count} memories")
        """
        params: dict[str, str | int] = {"limit": limit}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        response = self._http.get("/v1/memories/episodes", params=params)
        episodes = [Episode(**e) for e in response.get("episodes", [])]
        return EpisodeListResponse(
            count=response.get("count", 0),
            episodes=episodes,
        )

    def create_episode(self, entity_ids: list[str]) -> CreateEpisodeResponse:
        """
        Create a new episode from a list of entity IDs.

        Args:
            entity_ids: List of entity UUIDs to group into episode(s)

        Returns:
            CreateEpisodeResponse with created episodes

        Example:
            >>> result = client.memories.create_episode(["uuid1", "uuid2", "uuid3"])
            >>> print(f"Created {result.created} episodes")
        """
        response = self._http.post(
            "/v1/memories/episodes/create",
            json_data={"entity_ids": entity_ids},
        )
        episodes = [Episode(**e) for e in response.get("episodes", [])]
        return CreateEpisodeResponse(
            created=response.get("created", 0),
            episodes=episodes,
        )

    def consolidate(
        self,
        *,
        dry_run: bool = True,
        threshold_percentile: float = 30.0,
    ) -> ConsolidationResponse:
        """
        Run adaptive forgetting on memories.

        This consolidation process:
        1. Computes importance scores (recency + centrality + frequency)
        2. Soft-deletes low-importance memories (below threshold)
        3. Hard-deletes memories soft-deleted >30 days ago

        Args:
            dry_run: If True, preview changes without making them
            threshold_percentile: Percentile below which to soft-delete

        Returns:
            ConsolidationResponse with consolidation results

        Example:
            >>> # Preview what would be deleted
            >>> result = client.memories.consolidate(dry_run=True)
            >>> print(f"Would delete {result.entities_soft_deleted} memories")
            >>>
            >>> # Actually run consolidation
            >>> result = client.memories.consolidate(dry_run=False)
            >>> print(f"Reduced memory by {result.memory_reduction_pct}%")
        """
        response = self._http.post(
            "/v1/memories/consolidate",
            params={
                "dry_run": dry_run,
                "threshold_percentile": threshold_percentile,
            },
        )
        return ConsolidationResponse(**response)


class AsyncMemoriesResource:
    """Asynchronous memory operations."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def list(
        self,
        *,
        limit: int = 50,
        category: str | None = None,
        type: str | None = None,
    ) -> MemoryListResponse:
        """
        List all memories.

        Args:
            limit: Maximum number of memories to return
            category: Filter by category (personal, work, etc.)
            type: Filter by type (fact, concept, etc.)

        Returns:
            MemoryListResponse with count and list of memories
        """
        params: dict[str, str | int] = {"limit": limit}
        if category:
            params["category"] = category
        if type:
            params["type"] = type

        response = await self._http.get("/v1/memories", params=params)

        memories = [Memory(**m) for m in response.get("memories", [])]
        return MemoryListResponse(count=response.get("count", 0), memories=memories)

    async def list_direct(
        self,
        *,
        limit: int = 50,
        category: str | None = None,
    ) -> MemoryListResponse:
        """
        List direct memories (user-stated facts).

        Args:
            limit: Maximum number of memories to return
            category: Filter by category

        Returns:
            MemoryListResponse with count and list of direct memories
        """
        params: dict[str, str | int] = {"limit": limit}
        if category:
            params["category"] = category

        response = await self._http.get("/v1/memories/direct", params=params)

        memories = [Memory(**m) for m in response.get("memories", [])]
        return MemoryListResponse(count=response.get("count", 0), memories=memories)

    async def list_derived(self, *, limit: int = 50) -> DerivedMemoryListResponse:
        """
        List derived memories (AI-synthesized insights).

        Args:
            limit: Maximum number of memories to return

        Returns:
            DerivedMemoryListResponse with derivation information
        """
        response = await self._http.get("/v1/memories/derived", params={"limit": limit})

        memories = [DerivedMemory(**m) for m in response.get("memories", [])]
        return DerivedMemoryListResponse(count=response.get("count", 0), memories=memories)

    async def get(self, memory_id: str) -> Memory:
        """
        Get a specific memory by ID.

        Args:
            memory_id: UUID of the memory

        Returns:
            Memory object
        """
        response = await self._http.get(f"/v1/memories/{memory_id}")

        if response.get("derived_from"):
            return DerivedMemory(**response)
        return Memory(**response)

    async def delete(self, memory_id: str) -> None:
        """
        Delete a memory (soft delete).

        Args:
            memory_id: UUID of the memory
        """
        await self._http.delete(f"/v1/memories/{memory_id}")

    async def stats(self) -> MemoryStats:
        """
        Get memory statistics.

        Returns:
            MemoryStats with memory counts
        """
        response = await self._http.get("/v1/memories/stats/summary")
        return MemoryStats(**response)

    async def episodes(
        self,
        *,
        limit: int = 20,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> EpisodeListResponse:
        """
        List temporal episodes (time-windowed memory groups).

        Args:
            limit: Maximum number of episodes to return
            start_time: Filter by start time (ISO format)
            end_time: Filter by end time (ISO format)

        Returns:
            EpisodeListResponse with count and episodes
        """
        params: dict[str, str | int] = {"limit": limit}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        response = await self._http.get("/v1/memories/episodes", params=params)
        episodes = [Episode(**e) for e in response.get("episodes", [])]
        return EpisodeListResponse(
            count=response.get("count", 0),
            episodes=episodes,
        )

    async def create_episode(self, entity_ids: list[str]) -> CreateEpisodeResponse:
        """
        Create a new episode from a list of entity IDs.

        Args:
            entity_ids: List of entity UUIDs to group into episode(s)

        Returns:
            CreateEpisodeResponse with created episodes
        """
        response = await self._http.post(
            "/v1/memories/episodes/create",
            json_data={"entity_ids": entity_ids},
        )
        episodes = [Episode(**e) for e in response.get("episodes", [])]
        return CreateEpisodeResponse(
            created=response.get("created", 0),
            episodes=episodes,
        )

    async def consolidate(
        self,
        *,
        dry_run: bool = True,
        threshold_percentile: float = 30.0,
    ) -> ConsolidationResponse:
        """
        Run adaptive forgetting on memories.

        Args:
            dry_run: If True, preview changes without making them
            threshold_percentile: Percentile below which to soft-delete

        Returns:
            ConsolidationResponse with consolidation results
        """
        response = await self._http.post(
            "/v1/memories/consolidate",
            params={
                "dry_run": dry_run,
                "threshold_percentile": threshold_percentile,
            },
        )
        return ConsolidationResponse(**response)
