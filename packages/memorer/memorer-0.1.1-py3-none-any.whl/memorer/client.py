"""
Memoirer SDK Client

Main client class for interacting with the Memoirer API.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from memorer._http import AsyncHTTPClient, HTTPClient
from memorer.resources import (
    AsyncChatResource,
    AsyncEntitiesResource,
    AsyncKnowledgeResource,
    AsyncMemoriesResource,
    ChatResource,
    EntitiesResource,
    KnowledgeResource,
    MemoriesResource,
)
from memorer.types import HealthResponse

if TYPE_CHECKING:
    pass


@dataclass
class ClientConfig:
    """Configuration for Memoirer client."""

    api_key: str
    base_url: str = "https://api.memorer.ai"
    organization_id: str | None = None
    project_id: str | None = None
    timeout: float = 30.0
    max_retries: int = 3


class Memorer:
    """
    Memoirer SDK Client.

    The main entry point for interacting with the Memoirer API.
    Provides access to knowledge, entities, memories, and chat resources.

    Example:
        >>> from memorer import Memorer
        >>>
        >>> client = Memorer(api_key="your-api-key")
        >>>
        >>> # Ingest documents
        >>> client.knowledge.ingest(["AI agents need memory."])
        >>>
        >>> # Query with reasoning
        >>> result = client.knowledge.query("Why do AI agents need memory?")
        >>> print(result.answer)
        >>>
        >>> # Chat with streaming
        >>> for event in client.chat.send_message("Hello!", stream=True):
        ...     if event.type == "token":
        ...         print(event.content, end="")

    Attributes:
        knowledge: Knowledge graph operations (query, ingest, stats)
        entities: Entity CRUD operations
        memories: Memory management operations
        chat: Conversation and messaging with streaming
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        organization_id: str | None = None,
        project_id: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the Memoirer client.

        Args:
            api_key: Your Memoirer API key (JWT token). Can also be set via
                MEMORER_API_KEY environment variable.
            base_url: API base URL. Defaults to https://api.memorer.ai.
                Can also be set via MEMORER_BASE_URL environment variable.
            organization_id: Default organization ID to use for requests.
                Can be overridden per-request.
            project_id: Default project ID to use for requests.
                Can be overridden per-request.
            timeout: Request timeout in seconds. Default is 30.
            max_retries: Maximum number of retries for failed requests. Default is 3.

        Raises:
            ValueError: If no API key is provided.

        Example:
            >>> # Basic initialization
            >>> client = Memorer(api_key="your-api-key")
            >>>
            >>> # With organization context
            >>> client = Memorer(
            ...     api_key="your-api-key",
            ...     organization_id="org-uuid",
            ...     timeout=60.0,
            ... )
        """
        # Resolve API key
        resolved_api_key = api_key or os.environ.get("MEMORER_API_KEY")
        if not resolved_api_key:
            raise ValueError(
                "API key is required. Pass it as api_key argument or "
                "set MEMORER_API_KEY environment variable."
            )

        # Resolve base URL
        resolved_base_url = (
            base_url or os.environ.get("MEMORER_BASE_URL") or "https://api.memorer.ai"
        )

        # Create config
        self._config = ClientConfig(
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            organization_id=organization_id,
            project_id=project_id,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Create HTTP client
        self._http = HTTPClient(self._config)

        # Initialize resources
        self.knowledge = KnowledgeResource(self._http)
        self.entities = EntitiesResource(self._http)
        self.memories = MemoriesResource(self._http)
        self.chat = ChatResource(self._http)

    def health(self) -> HealthResponse:
        """
        Check API health status.

        Returns:
            HealthResponse with status and database connection info.

        Example:
            >>> health = client.health()
            >>> print(health.status)  # 'healthy', 'degraded', or 'unhealthy'
        """
        response = self._http.get("/health")
        return HealthResponse(**response)

    def close(self) -> None:
        """
        Close the client and release resources.

        Should be called when done using the client, or use as context manager.

        Example:
            >>> client = Memorer(api_key="...")
            >>> try:
            ...     # use client
            ... finally:
            ...     client.close()
        """
        self._http.close()

    def __enter__(self) -> Memorer:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class AsyncMemorer:
    """
    Async Memoirer SDK Client.

    Asynchronous version of the Memoirer client for use with asyncio.

    Example:
        >>> import asyncio
        >>> from memorer import AsyncMemorer
        >>>
        >>> async def main():
        ...     async with AsyncMemorer(api_key="your-api-key") as client:
        ...         result = await client.knowledge.query("What is AI?")
        ...         print(result.answer)
        >>>
        >>> asyncio.run(main())

    Attributes:
        knowledge: Async knowledge graph operations
        entities: Async entity CRUD operations
        memories: Async memory management operations
        chat: Async conversation and messaging with streaming
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        organization_id: str | None = None,
        project_id: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the async Memoirer client.

        Args:
            api_key: Your Memoirer API key (JWT token).
            base_url: API base URL. Defaults to https://api.memorer.ai.
            organization_id: Default organization ID to use for requests.
            project_id: Default project ID to use for requests.
            timeout: Request timeout in seconds. Default is 30.
            max_retries: Maximum number of retries. Default is 3.

        Raises:
            ValueError: If no API key is provided.
        """
        # Resolve API key
        resolved_api_key = api_key or os.environ.get("MEMORER_API_KEY")
        if not resolved_api_key:
            raise ValueError(
                "API key is required. Pass it as api_key argument or "
                "set MEMORER_API_KEY environment variable."
            )

        # Resolve base URL
        resolved_base_url = (
            base_url or os.environ.get("MEMORER_BASE_URL") or "https://api.memorer.ai"
        )

        # Create config
        self._config = ClientConfig(
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            organization_id=organization_id,
            project_id=project_id,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Create async HTTP client
        self._http = AsyncHTTPClient(self._config)

        # Initialize async resources
        self.knowledge = AsyncKnowledgeResource(self._http)
        self.entities = AsyncEntitiesResource(self._http)
        self.memories = AsyncMemoriesResource(self._http)
        self.chat = AsyncChatResource(self._http)

    async def health(self) -> HealthResponse:
        """
        Check API health status.

        Returns:
            HealthResponse with status and database connection info.
        """
        response = await self._http.get("/health")
        return HealthResponse(**response)

    async def close(self) -> None:
        """
        Close the client and release resources.
        """
        await self._http.close()

    async def __aenter__(self) -> AsyncMemorer:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
