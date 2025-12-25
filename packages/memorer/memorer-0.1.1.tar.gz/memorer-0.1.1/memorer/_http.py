"""
Memoirer SDK HTTP Client

Internal HTTP client wrapper using httpx.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, AsyncIterator, Iterator

import httpx

from memorer.errors import NetworkError, raise_for_status

if TYPE_CHECKING:
    from memorer.client import ClientConfig


class HTTPClient:
    """Synchronous HTTP client for Memoirer API."""

    def __init__(self, config: ClientConfig) -> None:
        self.config = config
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout),
                headers=self._build_headers(),
            )
        return self._client

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        if self.config.organization_id:
            headers["X-Organization-ID"] = self.config.organization_id
        if self.config.project_id:
            headers["X-Project-ID"] = self.config.project_id
        return headers

    def _merge_headers(self, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
        headers = self._build_headers()
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a synchronous HTTP request."""
        try:
            response = self.client.request(
                method=method,
                url=path,
                json=json_data,
                params=params,
                headers=self._merge_headers(headers),
            )
        except httpx.ConnectError as e:
            raise NetworkError(f"Failed to connect to {self.config.base_url}", detail=str(e))
        except httpx.TimeoutException as e:
            raise NetworkError("Request timed out", detail=str(e))
        except httpx.RequestError as e:
            raise NetworkError("Request failed", detail=str(e))

        # Handle empty responses (204 No Content)
        if response.status_code == 204:
            return {}

        # Parse response
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"error": response.text or "Unknown error"}

        # Raise for error status codes
        raise_for_status(response.status_code, data)

        return data

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("POST", path, json_data=json_data, params=params, headers=headers)

    def put(
        self,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("PUT", path, json_data=json_data, headers=headers)

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("DELETE", path, params=params, headers=headers)

    def stream_post(
        self,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Iterator[str]:
        """Make a streaming POST request, yielding raw SSE lines."""
        stream_headers = self._merge_headers(headers)
        stream_headers["Accept"] = "text/event-stream"

        try:
            with self.client.stream(
                "POST",
                path,
                json=json_data,
                headers=stream_headers,
            ) as response:
                # Check for error before streaming
                if response.status_code >= 400:
                    data = response.json()
                    raise_for_status(response.status_code, data)

                for line in response.iter_lines():
                    yield line
        except httpx.ConnectError as e:
            raise NetworkError(f"Failed to connect to {self.config.base_url}", detail=str(e))
        except httpx.TimeoutException as e:
            raise NetworkError("Request timed out", detail=str(e))
        except httpx.RequestError as e:
            raise NetworkError("Request failed", detail=str(e))

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None


class AsyncHTTPClient:
    """Asynchronous HTTP client for Memoirer API."""

    def __init__(self, config: ClientConfig) -> None:
        self.config = config
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout),
                headers=self._build_headers(),
            )
        return self._client

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        if self.config.organization_id:
            headers["X-Organization-ID"] = self.config.organization_id
        if self.config.project_id:
            headers["X-Project-ID"] = self.config.project_id
        return headers

    def _merge_headers(self, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
        headers = self._build_headers()
        if extra_headers:
            headers.update(extra_headers)
        return headers

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make an asynchronous HTTP request."""
        try:
            response = await self.client.request(
                method=method,
                url=path,
                json=json_data,
                params=params,
                headers=self._merge_headers(headers),
            )
        except httpx.ConnectError as e:
            raise NetworkError(f"Failed to connect to {self.config.base_url}", detail=str(e))
        except httpx.TimeoutException as e:
            raise NetworkError("Request timed out", detail=str(e))
        except httpx.RequestError as e:
            raise NetworkError("Request failed", detail=str(e))

        # Handle empty responses (204 No Content)
        if response.status_code == 204:
            return {}

        # Parse response
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"error": response.text or "Unknown error"}

        # Raise for error status codes
        raise_for_status(response.status_code, data)

        return data

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self.request("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self.request("POST", path, json_data=json_data, params=params, headers=headers)

    async def put(
        self,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self.request("PUT", path, json_data=json_data, headers=headers)

    async def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self.request("DELETE", path, params=params, headers=headers)

    async def stream_post(
        self,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> AsyncIterator[str]:
        """Make a streaming POST request, yielding raw SSE lines."""
        stream_headers = self._merge_headers(headers)
        stream_headers["Accept"] = "text/event-stream"

        try:
            async with self.client.stream(
                "POST",
                path,
                json=json_data,
                headers=stream_headers,
            ) as response:
                # Check for error before streaming
                if response.status_code >= 400:
                    data = response.json()
                    raise_for_status(response.status_code, data)

                async for line in response.aiter_lines():
                    yield line
        except httpx.ConnectError as e:
            raise NetworkError(f"Failed to connect to {self.config.base_url}", detail=str(e))
        except httpx.TimeoutException as e:
            raise NetworkError("Request timed out", detail=str(e))
        except httpx.RequestError as e:
            raise NetworkError("Request failed", detail=str(e))

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
