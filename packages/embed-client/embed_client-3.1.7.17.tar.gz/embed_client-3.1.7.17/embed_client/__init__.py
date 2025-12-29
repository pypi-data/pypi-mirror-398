"""
embed-client: Async client for Embedding Service API with comprehensive authentication, SSL/TLS, and mTLS support

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.config import ClientConfig
from embed_client.auth import ClientAuthManager
from embed_client.ssl_manager import ClientSSLManager
from embed_client.client_factory import ClientFactory
from embed_client.config_generator import ClientConfigGenerator
from embed_client.config_validator import ConfigValidator

__version__ = "3.1.7.8"
__all__ = [
    "EmbeddingServiceAsyncClient",
    "ClientConfig",
    "ClientAuthManager",
    "ClientSSLManager",
    "ClientFactory",
    "ClientConfigGenerator",
    "ConfigValidator",
]
