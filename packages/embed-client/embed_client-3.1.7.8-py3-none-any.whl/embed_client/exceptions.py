"""
Exception hierarchy for embed-client.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any


class EmbeddingServiceError(Exception):
    """Base exception for all embed-client errors."""


class EmbeddingServiceConnectionError(EmbeddingServiceError):
    """Raised when the service is unavailable or connection fails."""


class EmbeddingServiceHTTPError(EmbeddingServiceError):
    """
    Raised for HTTP errors (4xx, 5xx) returned by the underlying transport or adapter.

    Attributes:
        status: HTTP status code returned by the server.
        message: Human-readable error message describing the failure.
    """

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message


class EmbeddingServiceAPIError(EmbeddingServiceError):
    """
    Raised for errors returned by the Embedding Service API in the response body.

    The raw error payload from the API is stored in the ``error`` attribute.
    """

    def __init__(self, error: Any) -> None:
        super().__init__(f"API error: {error}")
        self.error = error


class EmbeddingServiceConfigError(EmbeddingServiceError):
    """Raised for configuration errors (invalid base_url, port, SSL settings, etc.)."""


class EmbeddingServiceTimeoutError(EmbeddingServiceError):
    """Raised when a request to the Embedding Service times out."""


class EmbeddingServiceJSONError(EmbeddingServiceError):
    """Raised when JSON parsing of a response body fails."""


__all__ = [
    "EmbeddingServiceError",
    "EmbeddingServiceConnectionError",
    "EmbeddingServiceHTTPError",
    "EmbeddingServiceAPIError",
    "EmbeddingServiceConfigError",
    "EmbeddingServiceTimeoutError",
    "EmbeddingServiceJSONError",
]
