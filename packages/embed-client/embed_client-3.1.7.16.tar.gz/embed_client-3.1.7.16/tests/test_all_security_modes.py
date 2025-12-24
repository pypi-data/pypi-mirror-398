#!/usr/bin/env python3
"""
Comprehensive Tests for All Security Modes
Tests all security modes using MCP Proxy Adapter framework:
- HTTP (no auth, with token, with roles)
- HTTPS (no auth, with token, with roles) 
- mTLS (no auth, with roles)

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import logging
import pytest
import pytest_asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add the framework to the path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent / ".venv" / "lib" / "python3.12" / "site-packages"),
)

from embed_client.async_client import (
    EmbeddingServiceAsyncClient,
    EmbeddingServiceAPIError,
    EmbeddingServiceHTTPError,
    EmbeddingServiceConnectionError,
    EmbeddingServiceTimeoutError,
    EmbeddingServiceJSONError,
    EmbeddingServiceConfigError,
)

# Test configurations for all security modes
TEST_CONFIGS = {
    # HTTP modes
    "http_simple": {
        "server": {"host": "localhost", "port": 10001},
        "auth": {"method": "none"},
        "ssl": {"enabled": False},
        "security": {"enabled": False},
    },
    "http_token": {
        "server": {"host": "localhost", "port": 10002},
        "auth": {"method": "api_key"},
        "ssl": {"enabled": False},
        "security": {
            "enabled": True,
            "tokens": {"admin": "admin-secret-key", "user": "user-secret-key"},
        },
    },
    "http_token_roles": {
        "server": {"host": "localhost", "port": 10003},
        "auth": {"method": "api_key"},
        "ssl": {"enabled": False},
        "security": {
            "enabled": True,
            "tokens": {
                "admin": "admin-secret-key",
                "user": "user-secret-key",
                "readonly": "readonly-secret-key",
            },
            "roles": {
                "admin": ["read", "write", "delete", "admin"],
                "user": ["read", "write"],
                "readonly": ["read"],
            },
        },
    },
    # HTTPS modes
    "https_simple": {
        "server": {"host": "localhost", "port": 10011},
        "auth": {"method": "none"},
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_NONE",
            "check_hostname": False,
            "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
            "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
        },
        "security": {"enabled": False},
    },
    "https_token": {
        "server": {"host": "localhost", "port": 10012},
        "auth": {"method": "api_key"},
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_NONE",
            "check_hostname": False,
            "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
            "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
        },
        "security": {
            "enabled": True,
            "tokens": {"admin": "admin-secret-key", "user": "user-secret-key"},
        },
    },
    "https_token_roles": {
        "server": {"host": "localhost", "port": 10013},
        "auth": {"method": "api_key"},
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_NONE",
            "check_hostname": False,
            "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
            "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
        },
        "security": {
            "enabled": True,
            "tokens": {
                "admin": "admin-secret-key",
                "user": "user-secret-key",
                "readonly": "readonly-secret-key",
            },
            "roles": {
                "admin": ["read", "write", "delete", "admin"],
                "user": ["read", "write"],
                "readonly": ["read"],
            },
        },
    },
    # mTLS modes
    "mtls_simple": {
        "server": {"host": "localhost", "port": 10021},
        "auth": {"method": "certificate"},
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
            "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
            "ca_cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/ca/ca.crt",
        },
        "transport": {"verify_client": True, "chk_hostname": True},
        "security": {"enabled": False},
    },
    "mtls_roles": {
        "server": {"host": "localhost", "port": 10022},
        "auth": {"method": "certificate"},
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
            "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
            "ca_cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/ca/ca.crt",
        },
        "transport": {"verify_client": True, "chk_hostname": True},
        "security": {
            "enabled": True,
            "roles": {
                "admin": ["read", "write", "delete", "admin"],
                "user": ["read", "write"],
                "readonly": ["read"],
            },
        },
    },
}


async def is_service_available(security_mode: str) -> bool:
    """Check if service is available for the given security mode."""
    config = TEST_CONFIGS[security_mode]
    try:
        async with EmbeddingServiceAsyncClient(config_dict=config) as client:
            await client.health()
        return True
    except Exception:
        return False


# Fixtures for each security mode
@pytest_asyncio.fixture
async def http_simple_client():
    """HTTP simple client fixture."""
    config = TEST_CONFIGS["http_simple"]
    async with EmbeddingServiceAsyncClient(config_dict=config) as client:
        yield client


@pytest_asyncio.fixture
async def http_token_client():
    """HTTP token client fixture."""
    config = TEST_CONFIGS["http_token"]
    async with EmbeddingServiceAsyncClient(config_dict=config) as client:
        yield client


@pytest_asyncio.fixture
async def http_token_roles_client():
    """HTTP token with roles client fixture."""
    config = TEST_CONFIGS["http_token_roles"]
    async with EmbeddingServiceAsyncClient(config_dict=config) as client:
        yield client


@pytest_asyncio.fixture
async def https_simple_client():
    """HTTPS simple client fixture."""
    config = TEST_CONFIGS["https_simple"]
    async with EmbeddingServiceAsyncClient(config_dict=config) as client:
        yield client


@pytest_asyncio.fixture
async def https_token_client():
    """HTTPS token client fixture."""
    config = TEST_CONFIGS["https_token"]
    async with EmbeddingServiceAsyncClient(config_dict=config) as client:
        yield client


@pytest_asyncio.fixture
async def https_token_roles_client():
    """HTTPS token with roles client fixture."""
    config = TEST_CONFIGS["https_token_roles"]
    async with EmbeddingServiceAsyncClient(config_dict=config) as client:
        yield client


@pytest_asyncio.fixture
async def mtls_simple_client():
    """mTLS simple client fixture."""
    config = TEST_CONFIGS["mtls_simple"]
    async with EmbeddingServiceAsyncClient(config_dict=config) as client:
        yield client


@pytest_asyncio.fixture
async def mtls_roles_client():
    """mTLS with roles client fixture."""
    config = TEST_CONFIGS["mtls_roles"]
    async with EmbeddingServiceAsyncClient(config_dict=config) as client:
        yield client


# HTTP Tests
@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_simple_health(http_simple_client):
    """Test HTTP simple health check."""
    if not await is_service_available("http_simple"):
        pytest.skip("HTTP simple service not available")

    result = await http_simple_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "healthy")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_simple_help(http_simple_client):
    """Test HTTP simple help command."""
    if not await is_service_available("http_simple"):
        pytest.skip("HTTP simple service not available")

    result = await http_simple_client.cmd("help")
    assert isinstance(result, dict)
    assert "success" in result or "commands" in result


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_simple_embed(http_simple_client):
    """Test HTTP simple embed command."""
    if not await is_service_available("http_simple"):
        pytest.skip("HTTP simple service not available")

    texts = ["hello world", "test embedding"]
    # Use error_policy=\"continue\" to follow embedding service contract
    params = {"texts": texts, "error_policy": "continue"}
    result = await http_simple_client.cmd("embed", params=params)
    assert isinstance(result, dict)
    assert "success" in result or "result" in result


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_token_health(http_token_client):
    """Test HTTP with token health check."""
    if not await is_service_available("http_token"):
        pytest.skip("HTTP token service not available")

    result = await http_token_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "healthy")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_token_help(http_token_client):
    """Test HTTP with token help command."""
    if not await is_service_available("http_token"):
        pytest.skip("HTTP token service not available")

    result = await http_token_client.cmd("help")
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_token_embed(http_token_client):
    """Test HTTP with token embed command."""
    if not await is_service_available("http_token"):
        pytest.skip("HTTP token service not available")

    texts = ["hello world", "test embedding"]
    params = {"texts": texts, "error_policy": "continue"}
    result = await http_token_client.cmd("embed", params=params)
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_token_roles_health(http_token_roles_client):
    """Test HTTP with token and roles health check."""
    if not await is_service_available("http_token_roles"):
        pytest.skip("HTTP token roles service not available")

    result = await http_token_roles_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "healthy")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_token_roles_help(http_token_roles_client):
    """Test HTTP with token and roles help command."""
    if not await is_service_available("http_token_roles"):
        pytest.skip("HTTP token roles service not available")

    result = await http_token_roles_client.cmd("help")
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_token_roles_embed(http_token_roles_client):
    """Test HTTP with token and roles embed command."""
    if not await is_service_available("http_token_roles"):
        pytest.skip("HTTP token roles service not available")

    texts = ["hello world", "test embedding"]
    params = {"texts": texts, "error_policy": "continue"}
    result = await http_token_roles_client.cmd("embed", params=params)
    assert isinstance(result, dict)


# HTTPS Tests
@pytest.mark.asyncio
@pytest.mark.integration
async def test_https_simple_health(https_simple_client):
    """Test HTTPS simple health check."""
    if not await is_service_available("https_simple"):
        pytest.skip("HTTPS simple service not available")

    result = await https_simple_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "healthy")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_https_simple_help(https_simple_client):
    """Test HTTPS simple help command."""
    if not await is_service_available("https_simple"):
        pytest.skip("HTTPS simple service not available")

    result = await https_simple_client.cmd("help")
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_https_simple_embed(https_simple_client):
    """Test HTTPS simple embed command."""
    if not await is_service_available("https_simple"):
        pytest.skip("HTTPS simple service not available")

    texts = ["hello world", "test embedding"]
    params = {"texts": texts, "error_policy": "continue"}
    result = await https_simple_client.cmd("embed", params=params)
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_https_token_health(https_token_client):
    """Test HTTPS with token health check."""
    if not await is_service_available("https_token"):
        pytest.skip("HTTPS token service not available")

    result = await https_token_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "healthy")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_https_token_help(https_token_client):
    """Test HTTPS with token help command."""
    if not await is_service_available("https_token"):
        pytest.skip("HTTPS token service not available")

    result = await https_token_client.cmd("help")
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_https_token_embed(https_token_client):
    """Test HTTPS with token embed command."""
    if not await is_service_available("https_token"):
        pytest.skip("HTTPS token service not available")

    texts = ["hello world", "test embedding"]
    params = {"texts": texts, "error_policy": "continue"}
    result = await https_token_client.cmd("embed", params=params)
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_https_token_roles_health(https_token_roles_client):
    """Test HTTPS with token and roles health check."""
    if not await is_service_available("https_token_roles"):
        pytest.skip("HTTPS token roles service not available")

    result = await https_token_roles_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "healthy")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_https_token_roles_help(https_token_roles_client):
    """Test HTTPS with token and roles help command."""
    if not await is_service_available("https_token_roles"):
        pytest.skip("HTTPS token roles service not available")

    result = await https_token_roles_client.cmd("help")
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_https_token_roles_embed(https_token_roles_client):
    """Test HTTPS with token and roles embed command."""
    if not await is_service_available("https_token_roles"):
        pytest.skip("HTTPS token roles service not available")

    texts = ["hello world", "test embedding"]
    params = {"texts": texts, "error_policy": "continue"}
    result = await https_token_roles_client.cmd("embed", params=params)
    assert isinstance(result, dict)


# mTLS Tests
@pytest.mark.asyncio
@pytest.mark.integration
async def test_mtls_simple_health(mtls_simple_client):
    """Test mTLS simple health check."""
    if not await is_service_available("mtls_simple"):
        pytest.skip("mTLS simple service not available")

    result = await mtls_simple_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "healthy")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mtls_simple_help(mtls_simple_client):
    """Test mTLS simple help command."""
    if not await is_service_available("mtls_simple"):
        pytest.skip("mTLS simple service not available")

    result = await mtls_simple_client.cmd("help")
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mtls_simple_embed(mtls_simple_client):
    """Test mTLS simple embed command."""
    if not await is_service_available("mtls_simple"):
        pytest.skip("mTLS simple service not available")

    texts = ["hello world", "test embedding"]
    params = {"texts": texts, "error_policy": "continue"}
    result = await mtls_simple_client.cmd("embed", params=params)
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mtls_roles_health(mtls_roles_client):
    """Test mTLS with roles health check."""
    if not await is_service_available("mtls_roles"):
        pytest.skip("mTLS roles service not available")

    result = await mtls_roles_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "healthy")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mtls_roles_help(mtls_roles_client):
    """Test mTLS with roles help command."""
    if not await is_service_available("mtls_roles"):
        pytest.skip("mTLS roles service not available")

    result = await mtls_roles_client.cmd("help")
    assert isinstance(result, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mtls_roles_embed(mtls_roles_client):
    """Test mTLS with roles embed command."""
    if not await is_service_available("mtls_roles"):
        pytest.skip("mTLS roles service not available")

    texts = ["hello world", "test embedding"]
    params = {"texts": texts}
    result = await mtls_roles_client.cmd("embed", params=params)
    assert isinstance(result, dict)


# Help command tests with parameters
@pytest.mark.asyncio
@pytest.mark.integration
async def test_help_with_parameters():
    """Test help command with parameters."""
    # Test with different security modes
    for mode in ["http_simple", "http_token", "https_simple", "mtls_simple"]:
        if await is_service_available(mode):
            config = TEST_CONFIGS[mode]
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                # Test help without parameters
                result = await client.cmd("help")
                assert isinstance(result, dict)

                # Test help with parameters (if supported)
                try:
                    result_with_params = await client.cmd("help", params={"command": "embed"})
                    assert isinstance(result_with_params, dict)
                except EmbeddingServiceAPIError:
                    # Some servers might not support parameters for help
                    pass


# Real server test on port 8001
@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_server_8001():
    """Test real server on port 8001."""
    real_config = {
        "server": {"host": "localhost", "port": 8001},
        "auth": {"method": "none"},
        "ssl": {"enabled": False},
        "security": {"enabled": False},
    }

    try:
        async with EmbeddingServiceAsyncClient(config_dict=real_config) as client:
            # Test health
            result = await client.health()
            assert "status" in result
            print(f"✅ Real server health: {result}")

            # Test help
            result = await client.cmd("help")
            assert isinstance(result, dict)
            print(f"✅ Real server help: {result}")

            # Test embed
            texts = ["hello world", "test embedding"]
            params = {"texts": texts}
            result = await client.cmd("embed", params=params)
            assert isinstance(result, dict)
            print(f"✅ Real server embed: {len(result)} keys in response")

    except Exception as e:
        pytest.skip(f"Real server on port 8001 not available: {e}")


# Error handling tests
@pytest.mark.asyncio
@pytest.mark.integration
async def test_error_handling():
    """Test error handling for invalid commands."""
    for mode in ["http_simple", "https_simple", "mtls_simple"]:
        if await is_service_available(mode):
            config = TEST_CONFIGS[mode]
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                # Test invalid command
                with pytest.raises(EmbeddingServiceAPIError):
                    await client.cmd("invalid_command")

                # Test empty texts
                with pytest.raises(EmbeddingServiceAPIError):
                    await client.cmd("embed", params={"texts": []})

            break  # Test only one mode for error handling


# Performance tests
@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.stress
async def test_performance():
    """Test performance with multiple requests."""
    for mode in ["http_simple", "https_simple", "mtls_simple"]:
        if await is_service_available(mode):
            config = TEST_CONFIGS[mode]
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                # Test multiple health checks
                start_time = time.time()
                for _ in range(10):
                    result = await client.health()
                    assert "status" in result
                end_time = time.time()

                print(f"✅ {mode}: 10 health checks in {end_time - start_time:.2f}s")

            break  # Test only one mode for performance
