"""
Helper functions for ClientFactory.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

from typing import Optional

from embed_client.client_factory import ClientFactory, SecurityMode
from embed_client.async_client import EmbeddingServiceAsyncClient


def create_client(
    base_url: str,
    port: int = 8001,
    auth_method: Optional[str] = None,
    ssl_enabled: Optional[bool] = None,
    **kwargs,
) -> EmbeddingServiceAsyncClient:
    """Create a client with automatic security mode detection."""
    return ClientFactory.create_client(
        base_url, port, auth_method, ssl_enabled, **kwargs
    )


def create_client_from_config(config_path: str) -> EmbeddingServiceAsyncClient:
    """Create client from configuration file."""
    return ClientFactory.from_config_file(config_path)


def create_client_from_env() -> EmbeddingServiceAsyncClient:
    """Create client from environment variables."""
    return ClientFactory.from_environment()


def detect_security_mode(
    base_url: str,
    auth_method: Optional[str] = None,
    ssl_enabled: Optional[bool] = None,
    cert_file: Optional[str] = None,
    key_file: Optional[str] = None,
    **kwargs,
) -> str:
    """Detect security mode based on provided parameters."""
    return ClientFactory.detect_security_mode(
        base_url, auth_method, ssl_enabled, cert_file, key_file, **kwargs
    )


__all__ = [
    "create_client",
    "create_client_from_config",
    "create_client_from_env",
    "detect_security_mode",
    "SecurityMode",
]
