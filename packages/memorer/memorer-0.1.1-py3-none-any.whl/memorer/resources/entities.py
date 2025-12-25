"""
Memoirer SDK Entities Resource

Entity CRUD operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from memorer.types import (
    BulkDeleteResponse,
    Entity,
    EntityListResponse,
    EntityRelationships,
    EntityUpdate,
)

if TYPE_CHECKING:
    from memorer._http import AsyncHTTPClient, HTTPClient


class EntitiesResource:
    """Synchronous entity operations."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        type: str | None = None,
    ) -> EntityListResponse:
        """
        List entities in the knowledge graph.

        Args:
            limit: Maximum number of entities to return (1-100)
            offset: Pagination offset
            type: Filter by entity type

        Returns:
            EntityListResponse with count and list of entities

        Example:
            >>> result = client.entities.list(limit=50)
            >>> for entity in result.entities:
            ...     print(f"{entity.type}: {entity.content}")
        """
        params = {"limit": limit, "offset": offset}
        if type:
            params["type"] = type

        response = self._http.get("/v1/knowledge/entities", params=params)

        # Convert response to proper types
        entities = [Entity(**e) for e in response.get("entities", [])]
        return EntityListResponse(count=response.get("count", 0), entities=entities)

    def get(self, entity_id: str) -> Entity:
        """
        Get a single entity by ID.

        Args:
            entity_id: UUID of the entity

        Returns:
            Entity object

        Raises:
            NotFoundError: If entity doesn't exist

        Example:
            >>> entity = client.entities.get("uuid-here")
            >>> print(entity.content)
        """
        response = self._http.get(f"/v1/knowledge/entities/{entity_id}")
        return Entity(**response)

    def update(
        self,
        entity_id: str,
        *,
        content: str | None = None,
        type: str | None = None,
        category: str | None = None,
        importance: float | None = None,
    ) -> Entity:
        """
        Update an entity.

        Args:
            entity_id: UUID of the entity
            content: New content
            type: New type
            category: New category
            importance: New importance score

        Returns:
            Updated entity

        Raises:
            NotFoundError: If entity doesn't exist

        Example:
            >>> entity = client.entities.update(
            ...     "uuid-here",
            ...     content="Updated content",
            ...     importance=0.9
            ... )
        """
        update = EntityUpdate(
            content=content,
            type=type,
            category=category,
            importance=importance,
        )
        data = update.model_dump(exclude_none=True)

        response = self._http.put(f"/v1/knowledge/entities/{entity_id}", json_data=data)
        return Entity(**response)

    def delete(self, entity_id: str) -> None:
        """
        Delete an entity (soft delete).

        Args:
            entity_id: UUID of the entity

        Raises:
            NotFoundError: If entity doesn't exist

        Example:
            >>> client.entities.delete("uuid-here")
        """
        self._http.delete(f"/v1/knowledge/entities/{entity_id}")

    def bulk_delete(self, entity_ids: list[str]) -> BulkDeleteResponse:
        """
        Delete multiple entities at once.

        Args:
            entity_ids: List of entity UUIDs to delete

        Returns:
            BulkDeleteResponse with deleted count and not found IDs

        Example:
            >>> result = client.entities.bulk_delete(["uuid-1", "uuid-2"])
            >>> print(f"Deleted {result.deleted} entities")
        """
        response = self._http.post(
            "/v1/knowledge/entities/bulk-delete",
            json_data={"entity_ids": entity_ids},
        )
        return BulkDeleteResponse(**response)

    def relationships(self, entity_id: str) -> EntityRelationships:
        """
        Get all relationships for an entity.

        Args:
            entity_id: UUID of the entity

        Returns:
            EntityRelationships with incoming and outgoing relationships

        Raises:
            NotFoundError: If entity doesn't exist

        Example:
            >>> rels = client.entities.relationships("uuid-here")
            >>> print(f"Outgoing: {len(rels.outgoing)}")
            >>> print(f"Incoming: {len(rels.incoming)}")
        """
        response = self._http.get(f"/v1/knowledge/entities/{entity_id}/relationships")
        return EntityRelationships(**response)


class AsyncEntitiesResource:
    """Asynchronous entity operations."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        type: str | None = None,
    ) -> EntityListResponse:
        """
        List entities in the knowledge graph.

        Args:
            limit: Maximum number of entities to return (1-100)
            offset: Pagination offset
            type: Filter by entity type

        Returns:
            EntityListResponse with count and list of entities
        """
        params = {"limit": limit, "offset": offset}
        if type:
            params["type"] = type

        response = await self._http.get("/v1/knowledge/entities", params=params)

        entities = [Entity(**e) for e in response.get("entities", [])]
        return EntityListResponse(count=response.get("count", 0), entities=entities)

    async def get(self, entity_id: str) -> Entity:
        """
        Get a single entity by ID.

        Args:
            entity_id: UUID of the entity

        Returns:
            Entity object
        """
        response = await self._http.get(f"/v1/knowledge/entities/{entity_id}")
        return Entity(**response)

    async def update(
        self,
        entity_id: str,
        *,
        content: str | None = None,
        type: str | None = None,
        category: str | None = None,
        importance: float | None = None,
    ) -> Entity:
        """
        Update an entity.

        Args:
            entity_id: UUID of the entity
            content: New content
            type: New type
            category: New category
            importance: New importance score

        Returns:
            Updated entity
        """
        update = EntityUpdate(
            content=content,
            type=type,
            category=category,
            importance=importance,
        )
        data = update.model_dump(exclude_none=True)

        response = await self._http.put(f"/v1/knowledge/entities/{entity_id}", json_data=data)
        return Entity(**response)

    async def delete(self, entity_id: str) -> None:
        """
        Delete an entity (soft delete).

        Args:
            entity_id: UUID of the entity
        """
        await self._http.delete(f"/v1/knowledge/entities/{entity_id}")

    async def bulk_delete(self, entity_ids: list[str]) -> BulkDeleteResponse:
        """
        Delete multiple entities at once.

        Args:
            entity_ids: List of entity UUIDs to delete

        Returns:
            BulkDeleteResponse with deleted count and not found IDs
        """
        response = await self._http.post(
            "/v1/knowledge/entities/bulk-delete",
            json_data={"entity_ids": entity_ids},
        )
        return BulkDeleteResponse(**response)

    async def relationships(self, entity_id: str) -> EntityRelationships:
        """
        Get all relationships for an entity.

        Args:
            entity_id: UUID of the entity

        Returns:
            EntityRelationships with incoming and outgoing relationships
        """
        response = await self._http.get(f"/v1/knowledge/entities/{entity_id}/relationships")
        return EntityRelationships(**response)
