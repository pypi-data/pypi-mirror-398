"""
Memoirer SDK Exceptions

Custom exception hierarchy for handling API errors.
"""

from typing import Any


class MemorerError(Exception):
    """Base exception for all Memoirer SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        detail: str | None = None,
        response: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail
        self.response = response

    def __str__(self) -> str:
        if self.detail:
            return f"{self.message}: {self.detail}"
        return self.message


class AuthenticationError(MemorerError):
    """Raised when authentication fails (401)."""

    def __init__(
        self,
        message: str = "Authentication failed",
        detail: str | None = None,
        response: Any = None,
    ) -> None:
        super().__init__(message, status_code=401, detail=detail, response=response)


class AuthorizationError(MemorerError):
    """Raised when authorization fails (403)."""

    def __init__(
        self,
        message: str = "Permission denied",
        detail: str | None = None,
        response: Any = None,
    ) -> None:
        super().__init__(message, status_code=403, detail=detail, response=response)


class NotFoundError(MemorerError):
    """Raised when a resource is not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        detail: str | None = None,
        response: Any = None,
    ) -> None:
        super().__init__(message, status_code=404, detail=detail, response=response)


class ValidationError(MemorerError):
    """Raised when request validation fails (400)."""

    def __init__(
        self,
        message: str = "Validation error",
        detail: str | None = None,
        response: Any = None,
    ) -> None:
        super().__init__(message, status_code=400, detail=detail, response=response)


class ConflictError(MemorerError):
    """Raised when there's a conflict with existing resource (409)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        detail: str | None = None,
        response: Any = None,
    ) -> None:
        super().__init__(message, status_code=409, detail=detail, response=response)


class RateLimitError(MemorerError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        detail: str | None = None,
        response: Any = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message, status_code=429, detail=detail, response=response)
        self.retry_after = retry_after


class ServerError(MemorerError):
    """Raised when server returns an error (5xx)."""

    def __init__(
        self,
        message: str = "Server error",
        status_code: int = 500,
        detail: str | None = None,
        response: Any = None,
    ) -> None:
        super().__init__(message, status_code=status_code, detail=detail, response=response)


class NetworkError(MemorerError):
    """Raised when there's a network connectivity issue."""

    def __init__(
        self,
        message: str = "Network error",
        detail: str | None = None,
    ) -> None:
        super().__init__(message, status_code=None, detail=detail)


class StreamingError(MemorerError):
    """Raised when streaming response fails."""

    def __init__(
        self,
        message: str = "Streaming error",
        detail: str | None = None,
    ) -> None:
        super().__init__(message, status_code=None, detail=detail)


def raise_for_status(status_code: int, response_data: dict[str, Any] | None = None) -> None:
    """
    Raise appropriate exception based on HTTP status code.

    Args:
        status_code: HTTP status code
        response_data: Optional response body as dict
    """
    if status_code < 400:
        return

    message = "API error"
    detail = None

    if response_data:
        message = response_data.get("error", message)
        detail = response_data.get("detail")

    if status_code == 400:
        raise ValidationError(message, detail=detail)
    elif status_code == 401:
        raise AuthenticationError(message, detail=detail)
    elif status_code == 403:
        raise AuthorizationError(message, detail=detail)
    elif status_code == 404:
        raise NotFoundError(message, detail=detail)
    elif status_code == 409:
        raise ConflictError(message, detail=detail)
    elif status_code == 429:
        retry_after = None
        if response_data:
            retry_after = response_data.get("retry_after")
        raise RateLimitError(message, detail=detail, retry_after=retry_after)
    elif status_code >= 500:
        raise ServerError(message, status_code=status_code, detail=detail)
    else:
        raise MemorerError(message, status_code=status_code, detail=detail)
