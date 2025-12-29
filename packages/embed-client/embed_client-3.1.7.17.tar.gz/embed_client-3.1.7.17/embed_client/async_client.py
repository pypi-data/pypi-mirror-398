"""
Async client for Embedding Service API (OpenAPI 3.0.2)

- 100% type-annotated
- English docstrings and examples
- Ready for PyPi
- Supports new API format with body, embedding, and chunks
- Supports all authentication methods (API Key, JWT, Basic Auth, Certificate)
- Integrates with mcp_security_framework
- Supports all security modes (HTTP, HTTPS, mTLS)

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional

import os

from embed_client.adapter_config_factory import AdapterConfigFactory
from embed_client.adapter_transport import AdapterTransport
from embed_client.auth import ClientAuthManager
from embed_client.config import ClientConfig
from embed_client.constants import (
    DEFAULT_BASE_URL,
    DEFAULT_PORT,
    EMBEDDING_SERVICE_BASE_URL_ENV,
    EMBEDDING_SERVICE_PORT_ENV,
)
from embed_client.exceptions import (
    EmbeddingServiceError,  # noqa: F401
    EmbeddingServiceHTTPError,  # noqa: F401
    EmbeddingServiceConnectionError,  # noqa: F401
    EmbeddingServiceConfigError,
    EmbeddingServiceTimeoutError,  # noqa: F401
    EmbeddingServiceAPIError,  # noqa: F401
    EmbeddingServiceJSONError,  # noqa: F401
)
from embed_client.async_client_api_mixin import AsyncClientAPIMixin
from embed_client.async_client_factory_mixin import AsyncClientFactoryMixin
from embed_client.async_client_introspection_mixin import AsyncClientIntrospectionMixin
from embed_client.async_client_lifecycle_mixin import AsyncClientLifecycleMixin
from embed_client.async_client_queue_mixin import AsyncClientQueueMixin
from embed_client.async_client_response_mixin import AsyncClientResponseMixin


class EmbeddingServiceAsyncClient(
    AsyncClientResponseMixin,
    AsyncClientLifecycleMixin,
    AsyncClientAPIMixin,
    AsyncClientQueueMixin,
    AsyncClientIntrospectionMixin,
    AsyncClientFactoryMixin,
):
    """
    Asynchronous client for the Embedding Service API.

    Supports both old and new API formats:
    - Old format: {"result": {"success": true, "data": {"embeddings": [...]}}}
    - New format: {
        "result": {
            "success": true,
            "data": {
                "embeddings": [...],
                "results": [
                    {
                        "body": "text",
                        "embedding": [...],
                        "tokens": [...],
                        "bm25_tokens": [...],
                    }
                ],
            },
        }
      }

    Supports all authentication methods and security modes:
    - API Key authentication
    - JWT token authentication
    - Basic authentication
    - Certificate authentication (mTLS)
    - HTTP, HTTPS, and mTLS security modes

    Args:
        base_url (str, optional): Base URL of the embedding service (e.g., "http://localhost").
        port (int, optional): Port of the embedding service (e.g., 8001).
        timeout (float): Request timeout in seconds (default: 30).
        config (ClientConfig, optional): Configuration object with authentication and SSL settings.
        config_dict (dict, optional): Configuration dictionary with authentication and SSL settings.
        auth_manager (ClientAuthManager, optional): Authentication manager instance.

    Raises:
        EmbeddingServiceConfigError: If base_url or port is invalid.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        port: Optional[int] = None,
        timeout: float = 30.0,
        config: Optional[ClientConfig] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        auth_manager: Optional[ClientAuthManager] = None,
    ):
        # Initialize configuration
        self.config = config
        self.config_dict = config_dict
        self.auth_manager = auth_manager

        # If config is provided, use it to set base_url and port
        if config:
            # Prefer explicit base_url from config if present
            config_base_url = config.get("server.base_url")
            server_host = config.get("server.host")
            server_port = config.get(
                "server.port",
                port or int(os.getenv(EMBEDDING_SERVICE_PORT_ENV, str(DEFAULT_PORT))),
            )
            ssl_enabled = config.get("ssl.enabled", False)

            if config_base_url:
                # Assume base_url already includes protocol and (optionally) port
                self.base_url = config_base_url
                self.port = server_port
            else:
                # Derive base_url from host and SSL settings
                host_value = (
                    server_host
                    or base_url
                    or os.getenv(EMBEDDING_SERVICE_BASE_URL_ENV, DEFAULT_BASE_URL)
                )
                protocol = "https" if ssl_enabled else "http"

                if isinstance(host_value, str) and (
                    host_value.startswith("http://")
                    or host_value.startswith("https://")
                ):
                    self.base_url = host_value
                else:
                    self.base_url = f"{protocol}://{host_value}"

                self.port = server_port

            self.timeout = config.get("client.timeout", timeout)
        elif config_dict:
            server_config = config_dict.get("server", {})
            # ✅ ИСПРАВЛЕНИЕ: Использовать base_url из конфигурации, если он есть
            if "base_url" in server_config:
                self.base_url = server_config["base_url"]
                self.port = None  # Порт уже включен в base_url
            else:
                host = server_config.get(
                    "host",
                    base_url
                    or os.getenv(EMBEDDING_SERVICE_BASE_URL_ENV, DEFAULT_BASE_URL),
                )
                port = server_config.get(
                    "port",
                    port
                    or int(os.getenv(EMBEDDING_SERVICE_PORT_ENV, str(DEFAULT_PORT))),
                )
                # Determine protocol from SSL config
                ssl_config = config_dict.get("ssl", {})
                protocol = "https" if ssl_config.get("enabled", False) else "http"
                # Create base_url from host and port
                if host.startswith("http://") or host.startswith("https://"):
                    self.base_url = host
                    self.port = port
                else:
                    self.base_url = f"{protocol}://{host}"
                    self.port = port
            self.timeout = config_dict.get("client", {}).get("timeout", timeout)
        else:
            # Use provided parameters or environment variables
            try:
                self.base_url = base_url or os.getenv(
                    EMBEDDING_SERVICE_BASE_URL_ENV, DEFAULT_BASE_URL
                )
            except (TypeError, AttributeError) as e:
                raise EmbeddingServiceConfigError(
                    f"Invalid base_url configuration: {e}"
                ) from e

            try:
                self.port = port or int(
                    os.getenv(EMBEDDING_SERVICE_PORT_ENV, str(DEFAULT_PORT))
                )
            except (ValueError, TypeError) as e:
                raise EmbeddingServiceConfigError(
                    f"Invalid port configuration: {e}"
                ) from e
            self.timeout = timeout

        # Validate base_url
        try:
            if not self.base_url:
                raise EmbeddingServiceConfigError("base_url must be provided.")
            if not isinstance(self.base_url, str):
                raise EmbeddingServiceConfigError("base_url must be a string.")

            # Validate URL format
            if not (
                self.base_url.startswith("http://")
                or self.base_url.startswith("https://")
            ):
                raise EmbeddingServiceConfigError(
                    "base_url must start with http:// or https://"
                )
        except (TypeError, AttributeError) as e:
            raise EmbeddingServiceConfigError(
                f"Invalid base_url configuration: {e}"
            ) from e

        # Validate port
        try:
            # ✅ ИСПРАВЛЕНИЕ: Порт не обязателен, если он уже в base_url
            if self.port is not None:
                if (
                    not isinstance(self.port, int)
                    or self.port <= 0
                    or self.port > 65535
                ):
                    raise EmbeddingServiceConfigError(
                        "port must be a valid integer between 1 and 65535."
                    )
        except (ValueError, TypeError) as e:
            raise EmbeddingServiceConfigError(f"Invalid port configuration: {e}") from e

        # Validate timeout
        try:
            self.timeout = float(self.timeout)
            if self.timeout <= 0:
                raise EmbeddingServiceConfigError("timeout must be positive.")
        except (ValueError, TypeError) as e:
            raise EmbeddingServiceConfigError(
                f"Invalid timeout configuration: {e}"
            ) from e

        # Store auth_manager if provided (for diagnostics only).
        # Actual authentication is handled by the adapter transport.
        self.auth_manager = auth_manager

        # Initialize adapter transport (always used) - this is the only transport.
        # Adapter reads config and handles all SSL/TLS, authentication, and queue operations.
        config_data = (
            self.config_dict
            if self.config_dict
            else (self.config.get_all() if self.config else {})
        )
        adapter_params = AdapterConfigFactory.from_config_dict(config_data)
        self._adapter_transport: AdapterTransport = AdapterTransport(adapter_params)

        # High-level API, queue, factory and diagnostic methods are
        # provided by mixin classes in async_client_*_mixin modules.


__all__ = [
    "EmbeddingServiceAsyncClient",
    "EmbeddingServiceError",
    "EmbeddingServiceHTTPError",
    "EmbeddingServiceConnectionError",
    "EmbeddingServiceConfigError",
    "EmbeddingServiceTimeoutError",
    "EmbeddingServiceAPIError",
    "EmbeddingServiceJSONError",
]
