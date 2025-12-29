"""
Test Phase 1: Adapter Compatibility Layer & Feature Flag

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import os
from typing import Dict, Any

from embed_client.adapter_config_factory import AdapterConfigFactory
from embed_client.config import ClientConfig
from embed_client.client_factory import ClientFactory
from embed_client.async_client import EmbeddingServiceAsyncClient


class TestAdapterConfigFactory:
    """Test AdapterConfigFactory translation."""

    def test_from_config_dict_http(self):
        """Test HTTP config translation."""
        config_dict = {
            "server": {"host": "http://localhost", "port": 8001},
            "client": {"timeout": 30.0},
        }

        adapter_params = AdapterConfigFactory.from_config_dict(config_dict)

        assert adapter_params["protocol"] == "http"
        assert adapter_params["host"] == "localhost"
        assert adapter_params["port"] == 8001
        assert adapter_params["timeout"] == 30.0
        assert adapter_params.get("token") is None

    def test_from_config_dict_https(self):
        """Test HTTPS config translation."""
        config_dict = {
            "server": {"host": "https://example.com", "port": 443},
            "ssl": {"enabled": True, "check_hostname": True},
            "client": {"timeout": 60.0},
        }

        adapter_params = AdapterConfigFactory.from_config_dict(config_dict)

        assert adapter_params["protocol"] == "https"
        assert adapter_params["host"] == "example.com"
        assert adapter_params["port"] == 443
        assert adapter_params["check_hostname"] is True

    def test_from_config_dict_mtls(self):
        """Test mTLS config translation."""
        config_dict = {
            "server": {"host": "https://secure.example.com", "port": 8443},
            "ssl": {
                "enabled": True,
                "cert_file": "/path/to/client.crt",
                "key_file": "/path/to/client.key",
                "ca_cert_file": "/path/to/ca.crt",
            },
            "client": {"timeout": 30.0},
        }

        adapter_params = AdapterConfigFactory.from_config_dict(config_dict)

        assert adapter_params["protocol"] == "mtls"
        assert adapter_params["cert"] == "/path/to/client.crt"
        assert adapter_params["key"] == "/path/to/client.key"
        assert adapter_params["ca"] == "/path/to/ca.crt"

    def test_from_config_dict_api_key_auth(self):
        """Test API key authentication translation."""
        config_dict = {
            "server": {"host": "http://localhost", "port": 8001},
            "auth": {
                "method": "api_key",
                "api_keys": {"user": "test-api-key-123"},
                "api_key_header": "X-API-Key",
            },
            "client": {"timeout": 30.0},
        }

        adapter_params = AdapterConfigFactory.from_config_dict(config_dict)

        assert adapter_params["token"] == "test-api-key-123"
        assert adapter_params["token_header"] == "X-API-Key"

    def test_from_client_config(self):
        """Test translation from ClientConfig object."""
        config = ClientConfig()
        # Use base_url for proper URL parsing
        config.set("server.base_url", "http://test.example.com:9000")
        config.set("client.timeout", 45.0)

        adapter_params = AdapterConfigFactory.from_client_config(config)

        # host should be extracted from URL
        assert adapter_params["host"] == "test.example.com"
        # Port should be from URL
        assert adapter_params["port"] == 9000
        assert adapter_params["timeout"] == 45.0

    def test_from_legacy_params(self):
        """Test translation from legacy factory parameters."""
        adapter_params = AdapterConfigFactory.from_legacy_params(
            base_url="https://api.example.com",
            port=443,
            auth_method="api_key",
            ssl_enabled=True,
            api_key="legacy-key-456",
            timeout=20.0,
        )

        assert adapter_params["protocol"] == "https"
        assert adapter_params["host"] == "api.example.com"
        assert adapter_params["port"] == 443
        assert adapter_params["token"] == "legacy-key-456"
        assert adapter_params["timeout"] == 20.0


class TestFeatureFlag:
    """Test feature flag functionality."""

    def test_config_has_client_timeout(self):
        """Test that ClientConfig includes client timeout."""
        config = ClientConfig()

        # Should have timeout in client section
        timeout = config.get("client.timeout")
        assert isinstance(timeout, (int, float))
        assert timeout > 0

    def test_client_factory_always_uses_adapter(self):
        """Test ClientFactory.create_client always uses adapter transport."""
        # Adapter transport is always used now
        client = ClientFactory.create_client(base_url="http://localhost", port=8001)

        assert client._adapter_transport is not None
        # Adapter transport should always be initialized
        assert hasattr(client, "_adapter_transport")


class TestClientAdapterIntegration:
    """Test client integration with adapter transport."""

    @pytest.mark.asyncio
    async def test_client_always_uses_adapter(self):
        """Test client always initializes adapter transport."""
        client = EmbeddingServiceAsyncClient(
            base_url="http://localhost",
            port=8001,
            config_dict={
                "server": {"host": "http://localhost", "port": 8001},
                "client": {"timeout": 30.0},
            },
        )

        # Adapter transport is always used now
        assert client._adapter_transport is not None

        # Test context manager
        async with client:
            assert client._adapter_transport is not None

    def test_adapter_transport_initialization(self):
        """Test AdapterTransport initialization."""
        from embed_client.adapter_transport import AdapterTransport

        adapter_params = {
            "protocol": "http",
            "host": "localhost",
            "port": 8001,
            "token_header": None,
            "token": None,
            "cert": None,
            "key": None,
            "ca": None,
            "check_hostname": False,
            "timeout": 30.0,
        }

        transport = AdapterTransport(adapter_params)

        assert transport.adapter_params == adapter_params
        assert transport._client is None  # Lazy initialization


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
