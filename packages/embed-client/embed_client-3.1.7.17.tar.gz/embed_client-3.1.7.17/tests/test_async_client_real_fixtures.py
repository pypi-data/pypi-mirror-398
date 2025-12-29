"""
Fixtures and helpers for real server integration tests.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import pytest_asyncio
from embed_client.async_client import EmbeddingServiceAsyncClient

# Test configurations for different security modes
TEST_CONFIGS = {
    "http": {
        "base_url": "http://localhost",
        "port": 8001,
        "config_dict": {
            "server": {"host": "http://localhost", "port": 8001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
        },
    },
    "https": {
        "base_url": "http://localhost",
        "port": 10043,
        "config_dict": {
            "server": {"host": "http://localhost", "port": 10043},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
        },
    },
    "mtls": {
        "base_url": "http://localhost",
        "port": 8001,
        "config_dict": {
            "server": {"host": "http://localhost", "port": 8001},
            "auth": {"method": "certificate"},
            "ssl": {"enabled": False},
            "security": {
                "enabled": True,
                "tokens": {},
                "roles": {
                    "admin": ["read", "write", "delete", "admin"],
                    "user": ["read", "write"],
                    "readonly": ["read"],
                },
            },
        },
    },
}


async def is_service_available(security_mode="http"):
    """Check if service is available for the given security mode."""
    config = TEST_CONFIGS[security_mode]
    try:
        async with EmbeddingServiceAsyncClient(
            config_dict=config["config_dict"]
        ) as client:
            await client.health()
        return True
    except Exception:
        return False


@pytest_asyncio.fixture
async def real_client():
    """Default HTTP client fixture."""
    config = TEST_CONFIGS["http"]
    async with EmbeddingServiceAsyncClient(config_dict=config["config_dict"]) as client:
        yield client


@pytest_asyncio.fixture
async def real_https_client():
    """HTTPS client fixture."""
    config = TEST_CONFIGS["https"]
    async with EmbeddingServiceAsyncClient(config_dict=config["config_dict"]) as client:
        yield client


@pytest_asyncio.fixture
async def real_mtls_client():
    """mTLS client fixture."""
    config = TEST_CONFIGS["mtls"]
    async with EmbeddingServiceAsyncClient(config_dict=config["config_dict"]) as client:
        yield client


def extract_vectors(result):
    """Extract vectors from API response, supporting both old and new formats."""
    # Handle direct embeddings field (old format compatibility)
    if "embeddings" in result:
        return result["embeddings"]

    # Handle result wrapper
    if "result" in result:
        res = result["result"]

        # Handle direct list in result (old format)
        if isinstance(res, list):
            return res

        if isinstance(res, dict):
            # Handle old format: result.embeddings
            if "embeddings" in res:
                return res["embeddings"]

            # Handle old format: result.data.embeddings
            if (
                "data" in res
                and isinstance(res["data"], dict)
                and "embeddings" in res["data"]
            ):
                return res["data"]["embeddings"]

            # Handle new format: result.data[].embedding
            if "data" in res and isinstance(res["data"], list):
                embeddings = []
                for item in res["data"]:
                    if isinstance(item, dict) and "embedding" in item:
                        embeddings.append(item["embedding"])
                    else:
                        pytest.fail(f"Invalid item format in new API response: {item}")
                return embeddings

    pytest.fail(f"Cannot extract embeddings from response: {result}")
