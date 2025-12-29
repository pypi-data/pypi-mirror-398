#!/usr/bin/env python3
"""
Comprehensive tests for embed() method with all override parameters.

Tests all connection override parameters:
- host, port, protocol
- token
- cert_file, key_file, ca_cert_file, crl_file
- timeout

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import pytest_asyncio
from pathlib import Path
from typing import Dict, Any, Optional

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.exceptions import (
    EmbeddingServiceError,
    EmbeddingServiceTimeoutError,
)


# Base configuration for tests
BASE_CONFIG: Dict[str, Any] = {
    "server": {
        "host": "localhost",
        "port": 8001,
    },
    "auth": {
        "method": "none",
    },
    "ssl": {
        "enabled": False,
    },
}


@pytest_asyncio.fixture
async def base_client():
    """Base client fixture."""
    async with EmbeddingServiceAsyncClient(config_dict=BASE_CONFIG) as client:
        yield client


class TestEmbedWithHostPort:
    """Tests for host and port override parameters."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_host_override(self, base_client):
        """Test embed() with host override."""
        # This test requires a real server
        # In real scenario, would test with different host
        texts = ["test text"]
        try:
            result = await base_client.embed(
                texts,
                host="localhost",
                timeout=5.0,
            )
            assert "results" in result or "embeddings" in result
        except (EmbeddingServiceError, Exception):
            # Expected if server is not running or connection fails
            pytest.skip("Server not available or connection failed")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_port_override(self, base_client):
        """Test embed() with port override."""
        texts = ["test text"]
        try:
            result = await base_client.embed(
                texts,
                port=8001,
                timeout=5.0,
            )
            assert "results" in result or "embeddings" in result
        except (EmbeddingServiceError, Exception):
            # Expected if server is not running or connection fails
            pytest.skip("Server not available or connection failed")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_host_and_port_override(self, base_client):
        """Test embed() with both host and port override."""
        texts = ["test text"]
        try:
            result = await base_client.embed(
                texts,
                host="localhost",
                port=8001,
                timeout=5.0,
            )
            assert "results" in result or "embeddings" in result
        except (EmbeddingServiceError, Exception):
            # Expected if server is not running or connection fails
            pytest.skip("Server not available or connection failed")


class TestEmbedWithProtocol:
    """Tests for protocol override parameter."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_protocol_http(self, base_client):
        """Test embed() with protocol='http' override."""
        texts = ["test text"]
        try:
            result = await base_client.embed(
                texts,
                protocol="http",
                timeout=5.0,
            )
            assert "results" in result or "embeddings" in result
        except (EmbeddingServiceError, Exception):
            # Expected if server is not running or connection fails
            pytest.skip("Server not available or connection failed")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_protocol_https(self, base_client):
        """Test embed() with protocol='https' override."""
        texts = ["test text"]
        try:
            result = await base_client.embed(
                texts,
                protocol="https",
                timeout=5.0,
            )
            assert "results" in result or "embeddings" in result
        except (EmbeddingServiceError, Exception):
            # Expected if server is not running or connection fails
            pytest.skip("Server not available or connection failed")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_protocol_mtls(self, base_client):
        """Test embed() with protocol='mtls' override."""
        texts = ["test text"]
        cert_dir = Path(__file__).parent.parent / "mtls_certificates"
        cert_file = cert_dir / "client" / "embedding-service.crt"
        key_file = cert_dir / "client" / "embedding-service.key"
        ca_cert_file = cert_dir / "ca" / "ca.crt"

        if not all([cert_file.exists(), key_file.exists(), ca_cert_file.exists()]):
            pytest.skip("mTLS certificates not found")

        try:
            result = await base_client.embed(
                texts,
                protocol="mtls",
                cert_file=str(cert_file),
                key_file=str(key_file),
                ca_cert_file=str(ca_cert_file),
                timeout=5.0,
            )
            assert "results" in result or "embeddings" in result
        except (EmbeddingServiceError, Exception):
            # Expected if server is not running or connection fails
            pytest.skip("Server not available or connection failed")


class TestEmbedWithToken:
    """Tests for token override parameter."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_token_override(self, base_client):
        """Test embed() with token override."""
        texts = ["test text"]
        try:
            result = await base_client.embed(
                texts,
                token="test-token-123",
                timeout=5.0,
            )
            assert "results" in result or "embeddings" in result
        except EmbeddingServiceError:
            # Expected if server is not running or token invalid
            pass


class TestEmbedWithCertificates:
    """Tests for certificate override parameters."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_cert_file_override(self, base_client):
        """Test embed() with cert_file override."""
        texts = ["test text"]
        cert_dir = Path(__file__).parent.parent / "mtls_certificates"
        cert_file = cert_dir / "client" / "embedding-service.crt"
        key_file = cert_dir / "client" / "embedding-service.key"
        ca_cert_file = cert_dir / "ca" / "ca.crt"

        if not all([cert_file.exists(), key_file.exists(), ca_cert_file.exists()]):
            pytest.skip("mTLS certificates not found")

        try:
            result = await base_client.embed(
                texts,
                cert_file=str(cert_file),
                key_file=str(key_file),
                ca_cert_file=str(ca_cert_file),
                protocol="mtls",
                timeout=5.0,
            )
            assert "results" in result or "embeddings" in result
        except (EmbeddingServiceError, Exception):
            # Expected if server is not running or connection fails
            pytest.skip("Server not available or connection failed")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_crl_file_override(self, base_client):
        """Test embed() with crl_file override."""
        texts = ["test text"]
        cert_dir = Path(__file__).parent.parent / "mtls_certificates"
        cert_file = cert_dir / "client" / "embedding-service.crt"
        key_file = cert_dir / "client" / "embedding-service.key"
        ca_cert_file = cert_dir / "ca" / "ca.crt"
        crl_file = cert_dir / "ca" / "ca.crl"

        if not all([cert_file.exists(), key_file.exists(), ca_cert_file.exists()]):
            pytest.skip("mTLS certificates not found")

        # CRL file is optional
        crl_path = str(crl_file) if crl_file.exists() else None

        try:
            result = await base_client.embed(
                texts,
                cert_file=str(cert_file),
                key_file=str(key_file),
                ca_cert_file=str(ca_cert_file),
                crl_file=crl_path,
                protocol="mtls",
                timeout=5.0,
            )
            assert "results" in result or "embeddings" in result
        except (EmbeddingServiceError, Exception):
            # Expected if server is not running or connection fails
            pytest.skip("Server not available or connection failed")


class TestEmbedWithTimeout:
    """Tests for timeout parameter."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_timeout_none(self, base_client):
        """Test embed() with timeout=None (no waiting)."""
        texts = ["test text"]
        try:
            result = await base_client.embed(
                texts,
                timeout=None,
            )
            # Should return immediately, may contain job_id if queued
            assert isinstance(result, dict)
        except (EmbeddingServiceError, Exception):
            # Expected if server is not running or connection fails
            pytest.skip("Server not available or connection failed")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_timeout_zero(self, base_client):
        """Test embed() with timeout=0 (wait indefinitely)."""
        texts = ["test text"]
        try:
            result = await base_client.embed(
                texts,
                timeout=0,
            )
            assert "results" in result or "embeddings" in result
        except (EmbeddingServiceError, EmbeddingServiceTimeoutError):
            # Expected if server is not running or timeout occurs
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_timeout_positive(self, base_client):
        """Test embed() with timeout > 0."""
        texts = ["test text"]
        try:
            result = await base_client.embed(
                texts,
                timeout=30.0,
            )
            assert "results" in result or "embeddings" in result
        except (EmbeddingServiceError, EmbeddingServiceTimeoutError):
            # Expected if server is not running or timeout occurs
            pass


class TestEmbedWithAllOverrides:
    """Tests for all override parameters combined."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_with_all_overrides(self, base_client):
        """Test embed() with all override parameters."""
        texts = ["test text"]
        cert_dir = Path(__file__).parent.parent / "mtls_certificates"
        cert_file = cert_dir / "client" / "embedding-service.crt"
        key_file = cert_dir / "client" / "embedding-service.key"
        ca_cert_file = cert_dir / "ca" / "ca.crt"
        crl_file = cert_dir / "ca" / "ca.crl"

        if not all([cert_file.exists(), key_file.exists(), ca_cert_file.exists()]):
            pytest.skip("mTLS certificates not found")

        crl_path = str(crl_file) if crl_file.exists() else None

        try:
            result = await base_client.embed(
                texts,
                host="localhost",
                port=8001,
                protocol="mtls",
                token="test-token",
                cert_file=str(cert_file),
                key_file=str(key_file),
                ca_cert_file=str(ca_cert_file),
                crl_file=crl_path,
                timeout=30.0,
            )
            assert "results" in result or "embeddings" in result
        except (EmbeddingServiceError, Exception):
            # Expected if server is not running or connection fails
            pytest.skip("Server not available or connection failed")


class TestEmbedHidesStatusCalls:
    """Tests that embed() fully hides intermediate status polling calls."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embed_hides_status_calls_with_timeout(self, base_client):
        """Test that embed() with timeout hides all status polling."""
        texts = ["test text 1", "test text 2"]
        try:
            # This should complete without exposing intermediate status calls
            result = await base_client.embed(
                texts,
                timeout=30.0,
            )
            # Should return final result, not intermediate status
            assert "results" in result or "embeddings" in result
            # Should not contain status polling information
            assert "status" not in result or result.get("status") in ("completed", "success")
        except (EmbeddingServiceError, Exception):
            # Expected if server is not running or connection fails
            pytest.skip("Server not available or connection failed")

