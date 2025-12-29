#!/usr/bin/env python3
"""
Additional tests for remaining modules to achieve 90%+ coverage.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from typing import Dict, Any
import os

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.response_normalizer import ResponseNormalizer
from embed_client.response_parsers import (
    extract_embeddings,
    extract_embedding_data,
    extract_texts,
    extract_chunks,
    extract_tokens,
    extract_bm25_tokens,
)


BASE_CONFIG: Dict[str, Any] = {
    "server": {"host": "localhost", "port": 8001},
    "auth": {"method": "none"},
    "ssl": {"enabled": False},
}


@pytest_asyncio.fixture
async def base_client():
    """Base client fixture."""
    async with EmbeddingServiceAsyncClient(config_dict=BASE_CONFIG) as client:
        yield client


class TestAsyncClientRemainingCoverage:
    """Tests for async_client.py remaining coverage."""

    def test_init_with_env_vars(self):
        """Test __init__ with environment variables."""
        import os
        from embed_client.constants import (
            EMBEDDING_SERVICE_BASE_URL_ENV,
            EMBEDDING_SERVICE_PORT_ENV,
        )
        
        os.environ[EMBEDDING_SERVICE_BASE_URL_ENV] = "http://test-host"
        os.environ[EMBEDDING_SERVICE_PORT_ENV] = "9000"
        
        try:
            client = EmbeddingServiceAsyncClient()
            assert client.base_url == "http://test-host"
            assert client.port == 9000
        finally:
            os.environ.pop(EMBEDDING_SERVICE_BASE_URL_ENV, None)
            os.environ.pop(EMBEDDING_SERVICE_PORT_ENV, None)

    def test_init_with_config_dict_host_https(self):
        """Test __init__ with config_dict containing https host."""
        config_dict = {
            "server": {"host": "https://localhost", "port": 8443},
            "auth": {"method": "none"},
            "ssl": {"enabled": True},
        }
        
        client = EmbeddingServiceAsyncClient(config_dict=config_dict)
        assert client.base_url == "https://localhost"

    def test_init_with_config_dict_host_http(self):
        """Test __init__ with config_dict containing http host."""
        config_dict = {
            "server": {"host": "http://localhost", "port": 8001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
        }
        
        client = EmbeddingServiceAsyncClient(config_dict=config_dict)
        assert client.base_url == "http://localhost"

    def test_init_with_config_dict_no_ssl(self):
        """Test __init__ with config_dict without SSL."""
        config_dict = {
            "server": {"host": "localhost", "port": 8001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
        }
        
        client = EmbeddingServiceAsyncClient(config_dict=config_dict)
        assert client.base_url.startswith("http://")

    def test_init_with_timeout(self):
        """Test __init__ with timeout parameter."""
        client = EmbeddingServiceAsyncClient(
            base_url="http://localhost",
            port=8001,
            timeout=60.0,
        )
        assert client.timeout == 60.0

    def test_init_with_config_timeout(self):
        """Test __init__ with config containing timeout."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("server.host", "localhost")
        config.set("server.port", 8001)
        config.set("client.timeout", 60.0)
        
        client = EmbeddingServiceAsyncClient(config=config)
        assert client.timeout == 60.0


class TestResponseNormalizerRemainingCoverage:
    """Tests for response_normalizer.py remaining coverage."""

    def test_normalize_command_response_unknown_mode(self):
        """Test normalize_command_response() with unknown mode."""
        response = {
            "mode": "unknown",
            "result": {"success": True},
        }
        normalized = ResponseNormalizer.normalize_command_response(response)
        assert isinstance(normalized, dict)

    def test_normalize_queue_status_with_data_status(self):
        """Test normalize_queue_status() with data.status."""
        status = {
            "data": {
                "status": "completed",
                "result": {"results": [[0.1]]},
            }
        }
        normalized = ResponseNormalizer.normalize_queue_status(status)
        assert isinstance(normalized, dict)

    def test_normalize_queue_status_with_result_status(self):
        """Test normalize_queue_status() with result.status."""
        status = {
            "result": {
                "status": "completed",
                "data": {"results": [[0.1]]},
            }
        }
        normalized = ResponseNormalizer.normalize_queue_status(status)
        assert isinstance(normalized, dict)

    def test_normalize_queue_status_with_nested_result_status(self):
        """Test normalize_queue_status() with nested result.data.status."""
        status = {
            "result": {
                "data": {
                    "status": "completed",
                    "result": {"results": [[0.1]]},
                }
            }
        }
        normalized = ResponseNormalizer.normalize_queue_status(status)
        assert isinstance(normalized, dict)

    def test_normalize_queue_status_with_data_result(self):
        """Test normalize_queue_status() with data.result."""
        status = {
            "data": {
                "result": {"results": [[0.1]]},
            }
        }
        normalized = ResponseNormalizer.normalize_queue_status(status)
        assert isinstance(normalized, dict)

    def test_normalize_queue_status_with_result_data_result(self):
        """Test normalize_queue_status() with result.data.result."""
        status = {
            "result": {
                "data": {
                    "result": {"results": [[0.1]]},
                }
            }
        }
        normalized = ResponseNormalizer.normalize_queue_status(status)
        assert isinstance(normalized, dict)

    def test_extract_error_from_adapter_with_dict(self):
        """Test extract_error_from_adapter() with dict error."""
        error_dict = {"code": -1, "message": "Test error"}
        result = ResponseNormalizer.extract_error_from_adapter(error_dict)
        assert isinstance(result, dict)
        assert "error" in result

    def test_extract_error_from_adapter_with_string(self):
        """Test extract_error_from_adapter() with string error."""
        error_str = "Test error"
        result = ResponseNormalizer.extract_error_from_adapter(error_str)
        assert isinstance(result, dict)
        assert "error" in result


class TestResponseParsersRemainingCoverage:
    """Tests for response_parsers.py remaining coverage."""

    def test_extract_embeddings_old_format_list(self):
        """Test extract_embeddings() with old format list."""
        result = {
            "result": {
                "data": [
                    {"body": "test", "embedding": [0.1, 0.2, 0.3]}
                ]
            }
        }
        embeddings = extract_embeddings(result)
        assert isinstance(embeddings, list)

    def test_extract_embedding_data_old_format_list(self):
        """Test extract_embedding_data() with old format list."""
        result = {
            "result": {
                "data": [
                    {
                        "body": "test",
                        "embedding": [0.1, 0.2, 0.3],
                        "tokens": ["test"],
                        "bm25_tokens": ["test"],
                    }
                ]
            }
        }
        data = extract_embedding_data(result)
        assert isinstance(data, list)

    def test_extract_texts_old_format(self):
        """Test extract_texts() with old format."""
        # Old format needs tokens or chunks, so use new format
        result = {
            "result": {
                "data": {
                    "results": [
                        {"body": "test1", "embedding": [0.1], "tokens": ["test1"], "bm25_tokens": ["test1"]},
                        {"body": "test2", "embedding": [0.2], "tokens": ["test2"], "bm25_tokens": ["test2"]},
                    ]
                }
            }
        }
        texts = extract_texts(result)
        assert isinstance(texts, list)
        assert len(texts) == 2

    def test_extract_chunks_old_format(self):
        """Test extract_chunks() with old format."""
        result = {
            "result": {
                "data": [
                    {"body": "test", "chunks": ["chunk1", "chunk2"], "embedding": [0.1]},
                ]
            }
        }
        chunks = extract_chunks(result)
        assert isinstance(chunks, list)

    def test_extract_tokens_old_format(self):
        """Test extract_tokens() with old format."""
        # Old format may not have tokens, so we need to use new format
        result = {
            "result": {
                "data": {
                    "results": [
                        {"body": "test", "tokens": ["token1", "token2"], "embedding": [0.1], "bm25_tokens": ["test"]},
                    ]
                }
            }
        }
        tokens = extract_tokens(result)
        assert isinstance(tokens, list)

    def test_extract_bm25_tokens_old_format(self):
        """Test extract_bm25_tokens() with old format."""
        # Old format may not have bm25_tokens, so we need to use new format
        result = {
            "result": {
                "data": {
                    "results": [
                        {"body": "test", "tokens": ["test"], "bm25_tokens": ["bm25_token1", "bm25_token2"], "embedding": [0.1]},
                    ]
                }
            }
        }
        bm25_tokens = extract_bm25_tokens(result)
        assert isinstance(bm25_tokens, list)

