"""
Shared constants for embed-client package.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

# Environment variable names for embedding service connection
EMBEDDING_SERVICE_BASE_URL_ENV: str = "EMBEDDING_SERVICE_BASE_URL"
EMBEDDING_SERVICE_PORT_ENV: str = "EMBEDDING_SERVICE_PORT"

# Default connection settings
DEFAULT_BASE_URL: str = "http://localhost"
DEFAULT_PORT: int = 8001

__all__ = [
    "EMBEDDING_SERVICE_BASE_URL_ENV",
    "EMBEDDING_SERVICE_PORT_ENV",
    "DEFAULT_BASE_URL",
    "DEFAULT_PORT",
]
