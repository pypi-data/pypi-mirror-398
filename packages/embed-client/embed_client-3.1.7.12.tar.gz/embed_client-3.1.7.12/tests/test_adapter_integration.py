"""
Integration test for adapter transport with real client usage patterns.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
from embed_client.client_factory import ClientFactory
from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.config import ClientConfig


class TestAdapterIntegration:
    """Integration tests for adapter transport."""

    def test_factory_creates_client_with_adapter(self):
        """Test that factory always creates client with adapter transport."""
        client = ClientFactory.create_client(base_url="http://localhost", port=8001)

        # Adapter transport is always used now
        assert client._adapter_transport is not None

    def test_client_from_config_always_uses_adapter(self):
        """Test creating client from config always uses adapter transport."""
        config_dict = {
            "server": {"host": "http://localhost", "port": 8001},
            "client": {"timeout": 30.0},
        }

        client = EmbeddingServiceAsyncClient(config_dict=config_dict)

        # Adapter transport is always used now
        assert client._adapter_transport is not None

    def test_all_security_modes_with_adapter(self):
        """Test that all security modes work with adapter transport."""
        security_modes = [
            ("http", "http://localhost", 8001, False, None, None),
            ("https", "https://localhost", 8443, True, None, None),
            (
                "mtls",
                "https://localhost",
                8443,
                True,
                "/path/to/cert.crt",
                "/path/to/key.key",
            ),
        ]

        for mode, base_url, port, ssl, cert, key in security_modes:
            client = ClientFactory.create_client(
                base_url=base_url,
                port=port,
                ssl_enabled=ssl,
                cert_file=cert,
                key_file=key,
            )

            # Adapter transport is always used
            assert client._adapter_transport is not None

    @pytest.mark.asyncio
    async def test_context_manager_with_adapter(self):
        """Test context manager with adapter transport."""
        client = EmbeddingServiceAsyncClient(
            config_dict={
                "server": {"host": "http://localhost", "port": 8001},
                "client": {"timeout": 30.0},
            }
        )

        async with client:
            assert client._adapter_transport is not None
            # Transport should be initialized
            assert hasattr(client._adapter_transport, "_client")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
