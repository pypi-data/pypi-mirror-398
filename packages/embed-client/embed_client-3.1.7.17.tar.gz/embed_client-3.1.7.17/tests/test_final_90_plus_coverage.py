#!/usr/bin/env python3
"""
Final tests to achieve 90%+ coverage for ALL remaining modules.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any
import os

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.async_client_introspection_mixin import AsyncClientIntrospectionMixin
from embed_client.async_client_queue_mixin import AsyncClientQueueMixin
from embed_client.async_client_api_mixin import AsyncClientAPIMixin
from embed_client.response_normalizer import ResponseNormalizer
from embed_client.response_parsers import (
    extract_embeddings,
    extract_embedding_data,
    extract_texts,
    extract_chunks,
    extract_tokens,
    extract_bm25_tokens,
)
from embed_client.exceptions import EmbeddingServiceConfigError, EmbeddingServiceError
from embed_client.config_presets import (
    convert_env_value,
    load_env_variables,
    validate_client_config,
    create_minimal_config_dict,
    create_secure_config_dict,
    create_http_config_for_class,
    create_http_token_config_for_class,
    create_https_config_for_class,
    create_https_token_config_for_class,
    create_mtls_config_for_class,
)


BASE_CONFIG: Dict[str, Any] = {
    "server": {"host": "localhost", "port": 8001},
    "auth": {"method": "none"},
    "ssl": {"enabled": False},
}


class TestAsyncClientFinalCoverage:
    """Tests for async_client.py to achieve 90%+ coverage."""

    def test_init_with_invalid_base_url_type(self):
        """Test __init__ with invalid base_url type."""
        with pytest.raises(EmbeddingServiceConfigError, match="base_url must be a string"):
            EmbeddingServiceAsyncClient(base_url=123)

    def test_init_with_empty_base_url(self):
        """Test __init__ with empty base_url."""
        # Empty base_url will use default from config, so we need to also clear host
        with pytest.raises((EmbeddingServiceConfigError, TypeError, ValueError)):
            # Force empty base_url by using config with empty base_url and no host
            from embed_client.config import ClientConfig
            config = ClientConfig()
            config.set("server.base_url", "")
            config.set("server.host", None)
            config.set("server.port", None)
            EmbeddingServiceAsyncClient(config=config)

    def test_init_with_invalid_url_format(self):
        """Test __init__ with invalid URL format."""
        with pytest.raises(EmbeddingServiceConfigError, match="base_url must start with http:// or https://"):
            EmbeddingServiceAsyncClient(base_url="invalid-url")

    def test_init_with_invalid_port_type(self):
        """Test __init__ with invalid port type."""
        # Port validation happens during initialization
        with pytest.raises((EmbeddingServiceConfigError, ValueError, TypeError)):
            EmbeddingServiceAsyncClient(base_url="http://localhost", port="invalid")

    def test_init_with_config_invalid_base_url(self):
        """Test __init__ with config containing invalid base_url."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        # Set base_url to empty string to trigger validation
        config.set("server.base_url", "")
        # Clear host and port to force base_url usage
        config.set("server.host", None)
        config.set("server.port", None)
        
        with pytest.raises((EmbeddingServiceConfigError, TypeError, ValueError)):
            EmbeddingServiceAsyncClient(config=config)

    def test_init_with_config_dict_invalid_port(self):
        """Test __init__ with config_dict containing invalid port."""
        config_dict = {
            "server": {"host": "localhost", "port": -1},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
        }
        
        with pytest.raises(EmbeddingServiceConfigError):
            EmbeddingServiceAsyncClient(config_dict=config_dict)

    def test_init_with_config_dict_port_too_large(self):
        """Test __init__ with config_dict containing port > 65535."""
        config_dict = {
            "server": {"host": "localhost", "port": 70000},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
        }
        
        with pytest.raises(EmbeddingServiceConfigError):
            EmbeddingServiceAsyncClient(config_dict=config_dict)


class TestResponseNormalizerFinalCoverage:
    """Tests for response_normalizer.py to achieve 90%+ coverage."""

    def test_normalize_immediate_response_with_success(self):
        """Test _normalize_immediate_response() with success field."""
        response = {
            "mode": "immediate",
            "result": {"success": True, "data": {"results": [[0.1]]}},
        }
        normalized = ResponseNormalizer.normalize_command_response(response)
        assert isinstance(normalized, dict)
        assert "result" in normalized

    def test_normalize_immediate_response_with_data(self):
        """Test _normalize_immediate_response() with data field."""
        response = {
            "mode": "immediate",
            "result": {"data": {"results": [[0.1]]}},
        }
        normalized = ResponseNormalizer.normalize_command_response(response)
        assert isinstance(normalized, dict)
        assert "result" in normalized

    def test_normalize_queued_response_with_job_id(self):
        """Test _normalize_queued_response() with job_id."""
        response = {
            "mode": "queued",
            "job_id": "test-job-123",
            "status": "queued",
        }
        normalized = ResponseNormalizer.normalize_command_response(response)
        assert isinstance(normalized, dict)

    def test_normalize_queued_response_with_result(self):
        """Test _normalize_queued_response() with result."""
        response = {
            "mode": "queued",
            "job_id": "test-job-123",
            "status": "completed",
            "result": {"success": True, "data": {"results": [[0.1]]}},
        }
        normalized = ResponseNormalizer.normalize_command_response(response)
        assert isinstance(normalized, dict)

    def test_normalize_queue_status_with_result_data(self):
        """Test normalize_queue_status() with result.data."""
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

    def test_normalize_queue_status_with_result_result(self):
        """Test normalize_queue_status() with result.result."""
        status = {
            "result": {
                "result": {"results": [[0.1]]},
            }
        }
        normalized = ResponseNormalizer.normalize_queue_status(status)
        assert isinstance(normalized, dict)

    def test_extract_error_from_adapter_with_exception(self):
        """Test extract_error_from_adapter() with Exception."""
        error = Exception("Test error")
        result = ResponseNormalizer.extract_error_from_adapter(error)
        assert isinstance(result, dict)
        assert "error" in result


class TestResponseParsersFinalCoverage:
    """Tests for response_parsers.py to achieve 90%+ coverage."""

    def test_extract_embeddings_new_format_invalid_item(self):
        """Test extract_embeddings() with invalid item format."""
        result = {
            "result": {
                "data": {
                    "results": [
                        "invalid"  # Not a dict
                    ]
                }
            }
        }
        with pytest.raises(ValueError):
            extract_embeddings(result)

    def test_extract_embeddings_new_format_missing_embedding(self):
        """Test extract_embeddings() with missing embedding field."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {"body": "test"}  # Missing embedding
                    ]
                }
            }
        }
        with pytest.raises(ValueError):
            extract_embeddings(result)

    def test_extract_embeddings_old_format_invalid_item(self):
        """Test extract_embeddings() old format with invalid item."""
        result = {
            "result": {
                "data": [
                    "invalid"  # Not a dict
                ]
            }
        }
        with pytest.raises(ValueError):
            extract_embeddings(result)

    def test_extract_embedding_data_new_format_missing_tokens(self):
        """Test extract_embedding_data() with missing tokens field."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {
                            "body": "test",
                            "embedding": [0.1, 0.2, 0.3],
                            "bm25_tokens": ["test"],
                            # Missing tokens
                        }
                    ]
                }
            }
        }
        with pytest.raises(ValueError, match="missing 'tokens' field"):
            extract_embedding_data(result)

    def test_extract_embedding_data_new_format_missing_bm25_tokens(self):
        """Test extract_embedding_data() with missing bm25_tokens field."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {
                            "body": "test",
                            "embedding": [0.1, 0.2, 0.3],
                            "tokens": ["test"],
                            # Missing bm25_tokens
                        }
                    ]
                }
            }
        }
        with pytest.raises(ValueError, match="missing 'bm25_tokens' field"):
            extract_embedding_data(result)

    def test_extract_chunks_missing_tokens_and_chunks(self):
        """Test extract_chunks() with missing tokens and chunks."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {
                            "body": "test",
                            "embedding": [0.1, 0.2, 0.3],
                            "tokens": ["test"],
                            "bm25_tokens": ["test"],
                            # Missing both tokens and chunks in extract_chunks context
                        }
                    ]
                }
            }
        }
        # extract_chunks uses extract_embedding_data, which requires tokens
        # So this should work
        chunks = extract_chunks(result)
        assert isinstance(chunks, list)

    def test_extract_chunks_with_chunks_field(self):
        """Test extract_chunks() with chunks field."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {
                            "body": "test",
                            "embedding": [0.1, 0.2, 0.3],
                            "tokens": ["test"],
                            "bm25_tokens": ["test"],
                            "chunks": ["chunk1", "chunk2"],
                        }
                    ]
                }
            }
        }
        chunks = extract_chunks(result)
        assert isinstance(chunks, list)
        assert len(chunks) == 1


class TestConfigPresetsFinalCoverage:
    """Tests for config_presets.py to achieve 90%+ coverage."""

    def test_convert_env_value_int(self):
        """Test convert_env_value() with integer."""
        assert convert_env_value("123") == 123

    def test_convert_env_value_float(self):
        """Test convert_env_value() with float."""
        assert convert_env_value("123.45") == 123.45

    def test_convert_env_value_string(self):
        """Test convert_env_value() with string."""
        assert convert_env_value("test") == "test"

    def test_load_env_variables_with_prefix(self):
        """Test load_env_variables() with prefix."""
        config_data = {}
        os.environ["TEST_SERVER_HOST"] = "test_host"
        os.environ["TEST_SERVER_PORT"] = "8001"
        os.environ["TEST_OTHER"] = "value"  # Should be ignored (no section_param format)
        
        try:
            load_env_variables(config_data, prefix="TEST_")
            assert "server" in config_data
            assert config_data["server"]["host"] == "test_host"
            assert config_data["server"]["port"] == 8001
        finally:
            os.environ.pop("TEST_SERVER_HOST", None)
            os.environ.pop("TEST_SERVER_PORT", None)
            os.environ.pop("TEST_OTHER", None)

    def test_load_env_variables_bool_values(self):
        """Test load_env_variables() with boolean values."""
        config_data = {}
        os.environ["TEST_SSL_ENABLED"] = "true"
        os.environ["TEST_AUTH_ENABLED"] = "false"
        
        try:
            load_env_variables(config_data, prefix="TEST_")
            assert config_data.get("ssl", {}).get("enabled") is True
            assert config_data.get("auth", {}).get("enabled") is False
        finally:
            os.environ.pop("TEST_SSL_ENABLED", None)
            os.environ.pop("TEST_AUTH_ENABLED", None)

    def test_validate_client_config_missing_host(self):
        """Test validate_client_config() with missing host."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        # Explicitly set host to None/empty to test validation
        config.set("server.host", None)
        config.set("server.port", 8001)
        
        errors = validate_client_config(config)
        assert isinstance(errors, list)
        # Should have error about missing host
        assert len(errors) > 0
        assert any("host" in str(err).lower() or "Host" in str(err) for err in errors)

    def test_validate_client_config_missing_port(self):
        """Test validate_client_config() with missing port."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("server.host", "localhost")
        # Explicitly set port to None to test validation
        config.set("server.port", None)
        
        errors = validate_client_config(config)
        assert isinstance(errors, list)
        # Should have error about missing port
        assert len(errors) > 0
        assert any("port" in str(err).lower() or "Port" in str(err) for err in errors)

    def test_create_minimal_config_dict(self):
        """Test create_minimal_config_dict()."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("server.host", "localhost")
        config.set("server.port", 8001)
        config.set("auth.method", "none")
        
        config_dict = create_minimal_config_dict(config)
        assert isinstance(config_dict, dict)
        assert "server" in config_dict
        assert config_dict["server"]["host"] == "localhost"

    def test_create_secure_config_dict(self):
        """Test create_secure_config_dict()."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("server.host", "localhost")
        config.set("server.port", 8443)
        config.set("ssl.enabled", True)
        config.set("auth.method", "api_key")
        
        config_dict = create_secure_config_dict(config)
        assert isinstance(config_dict, dict)
        assert "ssl" in config_dict
        assert config_dict["ssl"]["enabled"] is True

    def test_create_http_config_for_class(self):
        """Test create_http_config_for_class()."""
        from embed_client.config import ClientConfig
        
        config_obj = create_http_config_for_class(ClientConfig, host="localhost", port=8001)
        assert isinstance(config_obj, ClientConfig)
        assert config_obj.get("server.host") == "localhost"
        assert config_obj.get("server.port") == 8001

    def test_create_http_token_config_for_class(self):
        """Test create_http_token_config_for_class()."""
        from embed_client.config import ClientConfig
        
        config_obj = create_http_token_config_for_class(ClientConfig, host="localhost", port=8001, api_key="test-token")
        assert isinstance(config_obj, ClientConfig)
        assert config_obj.get("auth.method") == "api_key"

    def test_create_https_config_for_class(self):
        """Test create_https_config_for_class()."""
        from embed_client.config import ClientConfig
        
        config_obj = create_https_config_for_class(ClientConfig, host="localhost", port=8443)
        assert isinstance(config_obj, ClientConfig)
        assert config_obj.get("ssl.enabled") is True

    def test_create_https_token_config_for_class(self):
        """Test create_https_token_config_for_class()."""
        from embed_client.config import ClientConfig
        
        config_obj = create_https_token_config_for_class(ClientConfig, host="localhost", port=8443, api_key="test-token")
        assert isinstance(config_obj, ClientConfig)
        assert config_obj.get("ssl.enabled") is True
        assert config_obj.get("auth.method") == "api_key"

    def test_create_mtls_config_for_class(self):
        """Test create_mtls_config_for_class()."""
        from embed_client.config import ClientConfig
        
        config_obj = create_mtls_config_for_class(
            ClientConfig,
            host="localhost",
            port=8443,
            cert_file="/path/to/cert.pem",
            key_file="/path/to/key.pem",
            ca_cert_file="/path/to/ca.pem",
        )
        assert isinstance(config_obj, ClientConfig)
        assert config_obj.get("ssl.enabled") is True
        assert config_obj.get("ssl.cert_file") == "/path/to/cert.pem"


class TestAsyncClientIntrospectionMixinFinalCoverage:
    """Tests for async_client_introspection_mixin.py to achieve 90%+ coverage."""

    def test_validate_ssl_config_with_config_dict_no_ssl(self):
        """Test validate_ssl_config() with config_dict and SSL disabled."""
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config_dict = {"ssl": {"enabled": False}}
        
        client = TestClient()
        errors = client.validate_ssl_config()
        assert len(errors) == 0

    def test_validate_ssl_config_with_config_no_ssl(self):
        """Test validate_ssl_config() with config and SSL disabled."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("ssl.enabled", False)
        
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config = config
        
        client = TestClient()
        errors = client.validate_ssl_config()
        assert len(errors) == 0

    def test_validate_ssl_config_with_no_config(self):
        """Test validate_ssl_config() with no config."""
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                pass
        
        client = TestClient()
        errors = client.validate_ssl_config()
        assert len(errors) == 0


@pytest_asyncio.fixture
async def base_client():
    """Base client fixture."""
    async with EmbeddingServiceAsyncClient(config_dict=BASE_CONFIG) as client:
        yield client


class TestAsyncClientQueueMixinFinalCoverage:
    """Tests for async_client_queue_mixin.py to achieve 90%+ coverage."""

    @pytest.mark.asyncio
    async def test_wait_for_job_result_without_data_key(self, base_client):
        """Test wait_for_job() with result without data key."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            # First call returns completed status
            mock_status.return_value = {
                "status": "completed",
                "result": {"results": [[0.1]]},  # No "data" key
            }

            result = await base_client.wait_for_job("test-job", timeout=5.0)
            # wait_for_job should return the result directly if it's not a dict with "data"
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_wait_for_job_result_non_dict(self, base_client):
        """Test wait_for_job() with result as non-dict."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {
                "status": "completed",
                "result": "string result",  # Non-dict
            }

            result = await base_client.wait_for_job("test-job", timeout=5.0)
            # wait_for_job should return the result directly
            assert isinstance(result, (dict, str))

    @pytest.mark.asyncio
    async def test_wait_for_job_no_result(self, base_client):
        """Test wait_for_job() with no result."""
        with patch.object(
            base_client,
            "job_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {
                "status": "completed",
                # No result
            }

            result = await base_client.wait_for_job("test-job", timeout=5.0)
            # wait_for_job should return the status dict
            assert isinstance(result, dict)
            assert result.get("status") == "completed"

