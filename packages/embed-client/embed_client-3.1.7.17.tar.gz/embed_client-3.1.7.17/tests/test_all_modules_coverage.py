#!/usr/bin/env python3
"""
Comprehensive tests to achieve 90%+ coverage for ALL modules.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any
from pathlib import Path

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.async_client_introspection_mixin import AsyncClientIntrospectionMixin
from embed_client.async_client_lifecycle_mixin import AsyncClientLifecycleMixin
from embed_client.async_client_response_mixin import AsyncClientResponseMixin
from embed_client.response_normalizer import ResponseNormalizer
from embed_client.response_parsers import (
    extract_embeddings,
    extract_embedding_data,
    extract_texts,
    extract_chunks,
    extract_tokens,
    extract_bm25_tokens,
)
from embed_client.exceptions import (
    EmbeddingServiceError,
    EmbeddingServiceAPIError,
    EmbeddingServiceHTTPError,
    EmbeddingServiceConnectionError,
    EmbeddingServiceConfigError,
    EmbeddingServiceTimeoutError,
    EmbeddingServiceJSONError,
)
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
from embed_client import ssl_manager


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


class TestAsyncClientCoverage:
    """Tests for async_client.py to achieve 90%+ coverage."""

    def test_init_with_config(self):
        """Test __init__ with ClientConfig."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("server.host", "localhost")
        config.set("server.port", 8001)
        config.set("auth.method", "none")
        config.set("ssl.enabled", False)
        
        client = EmbeddingServiceAsyncClient(config=config)
        assert client.config is config

    def test_init_with_config_dict(self):
        """Test __init__ with config_dict."""
        config_dict = {
            "server": {"host": "localhost", "port": 8001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
        }
        
        client = EmbeddingServiceAsyncClient(config_dict=config_dict)
        assert client.config_dict == config_dict

    def test_init_with_base_url_and_port(self):
        """Test __init__ with base_url and port."""
        client = EmbeddingServiceAsyncClient(base_url="http://localhost", port=8001)
        assert client.base_url == "http://localhost"
        assert client.port == 8001

    def test_init_with_config_base_url(self):
        """Test __init__ with config containing base_url."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("server.base_url", "http://localhost:8001")
        config.set("server.port", 8001)
        config.set("ssl.enabled", False)
        
        client = EmbeddingServiceAsyncClient(config=config)
        assert client.base_url == "http://localhost:8001"

    def test_init_with_config_host_https(self):
        """Test __init__ with config containing https host."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("server.host", "localhost")
        config.set("server.port", 8443)
        config.set("ssl.enabled", True)
        # Clear base_url to force derivation from host and SSL
        config.set("server.base_url", None)
        
        client = EmbeddingServiceAsyncClient(config=config)
        assert client.base_url.startswith("https://")

    def test_init_with_config_dict_base_url(self):
        """Test __init__ with config_dict containing base_url."""
        config_dict = {
            "server": {"base_url": "http://localhost:8001"},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
        }
        
        client = EmbeddingServiceAsyncClient(config_dict=config_dict)
        assert client.base_url == "http://localhost:8001"

    def test_init_with_config_dict_https(self):
        """Test __init__ with config_dict containing https."""
        config_dict = {
            "server": {"host": "localhost", "port": 8443},
            "auth": {"method": "none"},
            "ssl": {"enabled": True},
        }
        
        client = EmbeddingServiceAsyncClient(config_dict=config_dict)
        assert client.base_url.startswith("https://")


class TestAsyncClientIntrospectionMixinCoverage:
    """Tests for async_client_introspection_mixin.py to achieve 90%+ coverage."""

    def test_get_auth_headers(self, base_client):
        """Test get_auth_headers()."""
        headers = base_client.get_auth_headers()
        assert isinstance(headers, dict)

    def test_is_authenticated_with_auth_manager(self):
        """Test is_authenticated() with auth_manager."""
        from embed_client.auth import ClientAuthManager
        
        auth_manager = ClientAuthManager({"auth": {"method": "api_key", "api_key": {"key": "test"}}})
        
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.auth_manager = auth_manager
        
        client = TestClient()
        assert client.is_authenticated() is True

    def test_is_authenticated_with_config_dict(self):
        """Test is_authenticated() with config_dict."""
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config_dict = {"auth": {"method": "api_key"}}
        
        client = TestClient()
        assert client.is_authenticated() is True

    def test_is_authenticated_with_config(self):
        """Test is_authenticated() with config."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("auth.method", "api_key")
        
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config = config
        
        client = TestClient()
        assert client.is_authenticated() is True

    def test_get_auth_method_with_auth_manager(self):
        """Test get_auth_method() with auth_manager."""
        from embed_client.auth import ClientAuthManager
        
        auth_manager = ClientAuthManager({"auth": {"method": "jwt"}})
        
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.auth_manager = auth_manager
        
        client = TestClient()
        assert client.get_auth_method() == "jwt"

    def test_get_auth_method_with_config_dict(self):
        """Test get_auth_method() with config_dict."""
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config_dict = {"auth": {"method": "basic"}}
        
        client = TestClient()
        assert client.get_auth_method() == "basic"

    def test_get_auth_method_with_config(self):
        """Test get_auth_method() with config."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("auth.method", "certificate")
        
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config = config
        
        client = TestClient()
        assert client.get_auth_method() == "certificate"

    def test_is_ssl_enabled_with_config_dict(self):
        """Test is_ssl_enabled() with config_dict."""
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config_dict = {"ssl": {"enabled": True}}
        
        client = TestClient()
        assert client.is_ssl_enabled() is True

    def test_is_ssl_enabled_with_config(self):
        """Test is_ssl_enabled() with config."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("ssl.enabled", True)
        
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config = config
        
        client = TestClient()
        assert client.is_ssl_enabled() is True

    def test_is_mtls_enabled_with_config_dict(self):
        """Test is_mtls_enabled() with config_dict."""
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config_dict = {
                    "ssl": {
                        "enabled": True,
                        "cert_file": "/path/to/cert.pem",
                        "key_file": "/path/to/key.pem",
                    }
                }
        
        client = TestClient()
        assert client.is_mtls_enabled() is True

    def test_is_mtls_enabled_with_config(self):
        """Test is_mtls_enabled() with config."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("ssl.enabled", True)
        config.set("ssl.cert_file", "/path/to/cert.pem")
        config.set("ssl.key_file", "/path/to/key.pem")
        
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config = config
        
        client = TestClient()
        assert client.is_mtls_enabled() is True

    def test_get_ssl_config_with_config_dict(self):
        """Test get_ssl_config() with config_dict."""
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config_dict = {"ssl": {"enabled": True, "cert_file": "/path/to/cert.pem"}}
        
        client = TestClient()
        ssl_config = client.get_ssl_config()
        assert isinstance(ssl_config, dict)
        assert ssl_config.get("enabled") is True

    def test_get_ssl_config_with_config(self):
        """Test get_ssl_config() with config."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("ssl.enabled", True)
        
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config = config
        
        client = TestClient()
        ssl_config = client.get_ssl_config()
        assert isinstance(ssl_config, dict)

    def test_validate_ssl_config_with_missing_files(self):
        """Test validate_ssl_config() with missing certificate files."""
        class TestClient(AsyncClientIntrospectionMixin):
            def __init__(self):
                self.config_dict = {
                    "ssl": {
                        "enabled": True,
                        "cert_file": "/nonexistent/cert.pem",
                        "key_file": "/nonexistent/key.pem",
                        "ca_cert_file": "/nonexistent/ca.pem",
                    }
                }
        
        client = TestClient()
        errors = client.validate_ssl_config()
        assert len(errors) > 0

    def test_validate_ssl_config_with_valid_files(self):
        """Test validate_ssl_config() with valid certificate files."""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cert_file = os.path.join(tmpdir, "cert.pem")
            key_file = os.path.join(tmpdir, "key.pem")
            ca_file = os.path.join(tmpdir, "ca.pem")
            
            for f in [cert_file, key_file, ca_file]:
                with open(f, "w") as fp:
                    fp.write("test")
            
            class TestClient(AsyncClientIntrospectionMixin):
                def __init__(self):
                    self.config_dict = {
                        "ssl": {
                            "enabled": True,
                            "cert_file": cert_file,
                            "key_file": key_file,
                            "ca_cert_file": ca_file,
                        }
                    }
            
            client = TestClient()
            errors = client.validate_ssl_config()
            assert len(errors) == 0

    def test_get_supported_ssl_protocols(self, base_client):
        """Test get_supported_ssl_protocols()."""
        protocols = base_client.get_supported_ssl_protocols()
        assert isinstance(protocols, list)
        assert "TLSv1.2" in protocols
        assert "TLSv1.3" in protocols


class TestAsyncClientLifecycleMixinCoverage:
    """Tests for async_client_lifecycle_mixin.py to achieve 90%+ coverage."""

    @pytest.mark.asyncio
    async def test_aenter_with_exception(self):
        """Test __aenter__() with exception."""
        class TestClient(AsyncClientLifecycleMixin):
            def __init__(self):
                self._adapter_transport = AsyncMock()
                self._adapter_transport.__aenter__ = AsyncMock(side_effect=Exception("Test error"))
        
        client = TestClient()
        with pytest.raises(EmbeddingServiceError, match="Failed to create transport"):
            await client.__aenter__()

    @pytest.mark.asyncio
    async def test_aexit_with_no_transport(self):
        """Test __aexit__() with no transport."""
        class TestClient(AsyncClientLifecycleMixin):
            def __init__(self):
                self._adapter_transport = None
        
        client = TestClient()
        await client.__aexit__(None, None, None)  # Should not raise

    @pytest.mark.asyncio
    async def test_aexit_with_exception(self):
        """Test __aexit__() with exception."""
        class TestClient(AsyncClientLifecycleMixin):
            def __init__(self):
                self._adapter_transport = AsyncMock()
                self._adapter_transport.__aexit__ = AsyncMock(side_effect=Exception("Test error"))
        
        client = TestClient()
        with pytest.raises(EmbeddingServiceError, match="Failed to close adapter transport"):
            await client.__aexit__(None, None, None)

    @pytest.mark.asyncio
    async def test_close_with_no_transport(self):
        """Test close() with no transport."""
        class TestClient(AsyncClientLifecycleMixin):
            def __init__(self):
                self._adapter_transport = None
        
        client = TestClient()
        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_close_with_exception(self):
        """Test close() with exception."""
        class TestClient(AsyncClientLifecycleMixin):
            def __init__(self):
                self._adapter_transport = AsyncMock()
                self._adapter_transport.close = AsyncMock(side_effect=Exception("Test error"))
        
        client = TestClient()
        with pytest.raises(EmbeddingServiceError, match="Failed to close adapter transport"):
            await client.close()


class TestAsyncClientResponseMixinCoverage:
    """Tests for async_client_response_mixin.py to achieve 90%+ coverage."""

    def test_format_error_response(self, base_client):
        """Test _format_error_response()."""
        response = base_client._format_error_response("Test error", lang="en", text="test")
        assert isinstance(response, dict)
        assert "error" in response
        assert response.get("lang") == "en"
        assert response.get("text") == "test"

    def test_extract_embeddings(self, base_client):
        """Test extract_embeddings()."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {"body": "test", "embedding": [0.1, 0.2, 0.3]}
                    ]
                }
            }
        }
        embeddings = base_client.extract_embeddings(result)
        assert isinstance(embeddings, list)
        assert len(embeddings) == 1

    def test_extract_embedding_data(self, base_client):
        """Test extract_embedding_data()."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {
                            "body": "test",
                            "embedding": [0.1, 0.2, 0.3],
                            "tokens": ["test"],
                            "bm25_tokens": ["test"],
                        }
                    ]
                }
            }
        }
        data = base_client.extract_embedding_data(result)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_extract_texts(self, base_client):
        """Test extract_texts()."""
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
        texts = base_client.extract_texts(result)
        assert isinstance(texts, list)
        assert len(texts) == 2

    def test_extract_chunks(self, base_client):
        """Test extract_chunks()."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {"body": "test", "chunks": ["chunk1", "chunk2"], "embedding": [0.1], "tokens": ["test"], "bm25_tokens": ["test"]},
                    ]
                }
            }
        }
        chunks = base_client.extract_chunks(result)
        assert isinstance(chunks, list)
        assert len(chunks) == 1

    def test_extract_tokens(self, base_client):
        """Test extract_tokens()."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {"body": "test", "tokens": ["token1", "token2"], "embedding": [0.1], "bm25_tokens": ["test"]},
                    ]
                }
            }
        }
        tokens = base_client.extract_tokens(result)
        assert isinstance(tokens, list)
        assert len(tokens) == 1

    def test_extract_bm25_tokens(self, base_client):
        """Test extract_bm25_tokens()."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {"body": "test", "bm25_tokens": ["bm25_token1", "bm25_token2"], "embedding": [0.1], "tokens": ["test"]},
                    ]
                }
            }
        }
        bm25_tokens = base_client.extract_bm25_tokens(result)
        assert isinstance(bm25_tokens, list)
        assert len(bm25_tokens) == 1


class TestResponseNormalizerCoverage:
    """Tests for response_normalizer.py to achieve 90%+ coverage."""

    def test_normalize_command_response_immediate(self):
        """Test normalize_command_response() with immediate mode."""
        response = {
            "mode": "immediate",
            "result": {"success": True, "data": {"results": [[0.1]]}},
        }
        normalized = ResponseNormalizer.normalize_command_response(response)
        assert isinstance(normalized, dict)

    def test_normalize_command_response_queued(self):
        """Test normalize_command_response() with queued mode."""
        response = {
            "mode": "queued",
            "job_id": "test-job-123",
            "status": "completed",
        }
        normalized = ResponseNormalizer.normalize_command_response(response)
        assert isinstance(normalized, dict)

    def test_normalize_queue_status(self):
        """Test normalize_queue_status()."""
        status = {
            "status": "completed",
            "result": {"data": {"results": [[0.1]]}},
        }
        normalized = ResponseNormalizer.normalize_queue_status(status)
        assert isinstance(normalized, dict)

    def test_extract_error_from_adapter(self):
        """Test extract_error_from_adapter()."""
        error = Exception("Test error")
        error_dict = ResponseNormalizer.extract_error_from_adapter(error)
        assert isinstance(error_dict, dict)
        assert "error" in error_dict


class TestResponseParsersCoverage:
    """Tests for response_parsers.py to achieve 90%+ coverage."""

    def test_extract_embeddings_new_format(self):
        """Test extract_embeddings() with new format."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {"body": "test", "embedding": [0.1, 0.2, 0.3]}
                    ]
                }
            }
        }
        embeddings = extract_embeddings(result)
        assert isinstance(embeddings, list)
        assert len(embeddings) == 1

    def test_extract_embeddings_old_format(self):
        """Test extract_embeddings() with old format."""
        result = {
            "result": {
                "data": [
                    {"body": "test", "embedding": [0.1, 0.2, 0.3]}
                ]
            }
        }
        embeddings = extract_embeddings(result)
        assert isinstance(embeddings, list)
        assert len(embeddings) == 1

    def test_extract_embedding_data_new_format(self):
        """Test extract_embedding_data() with new format."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {
                            "body": "test",
                            "embedding": [0.1, 0.2, 0.3],
                            "tokens": ["test"],
                            "bm25_tokens": ["test"],
                        }
                    ]
                }
            }
        }
        data = extract_embedding_data(result)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_extract_embedding_data_old_format(self):
        """Test extract_embedding_data() with old format."""
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
        assert len(data) == 1

    def test_extract_texts(self):
        """Test extract_texts()."""
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

    def test_extract_chunks(self):
        """Test extract_chunks()."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {"body": "test", "chunks": ["chunk1", "chunk2"], "embedding": [0.1], "tokens": ["test"], "bm25_tokens": ["test"]},
                    ]
                }
            }
        }
        chunks = extract_chunks(result)
        assert isinstance(chunks, list)
        assert len(chunks) == 1

    def test_extract_tokens(self):
        """Test extract_tokens()."""
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
        assert len(tokens) == 1

    def test_extract_bm25_tokens(self):
        """Test extract_bm25_tokens()."""
        result = {
            "result": {
                "data": {
                    "results": [
                        {"body": "test", "bm25_tokens": ["bm25_token1", "bm25_token2"], "embedding": [0.1], "tokens": ["test"]},
                    ]
                }
            }
        }
        bm25_tokens = extract_bm25_tokens(result)
        assert isinstance(bm25_tokens, list)
        assert len(bm25_tokens) == 1


class TestExceptionsCoverage:
    """Tests for exceptions.py to achieve 90%+ coverage."""

    def test_embedding_service_error(self):
        """Test EmbeddingServiceError."""
        error = EmbeddingServiceError("Test error")
        assert str(error) == "Test error"

    def test_embedding_service_api_error(self):
        """Test EmbeddingServiceAPIError."""
        error = EmbeddingServiceAPIError({"message": "Test error"})
        assert "Test error" in str(error)

    def test_embedding_service_http_error(self):
        """Test EmbeddingServiceHTTPError."""
        error = EmbeddingServiceHTTPError(404, "Test error")
        assert "Test error" in str(error)
        assert error.status == 404

    def test_embedding_service_connection_error(self):
        """Test EmbeddingServiceConnectionError."""
        error = EmbeddingServiceConnectionError("Test error")
        assert "Test error" in str(error)

    def test_embedding_service_config_error(self):
        """Test EmbeddingServiceConfigError."""
        error = EmbeddingServiceConfigError("Test error")
        assert "Test error" in str(error)

    def test_embedding_service_timeout_error(self):
        """Test EmbeddingServiceTimeoutError."""
        error = EmbeddingServiceTimeoutError("Test error")
        assert "Test error" in str(error)

    def test_embedding_service_json_error(self):
        """Test EmbeddingServiceJSONError."""
        error = EmbeddingServiceJSONError("Test error")
        assert "Test error" in str(error)


class TestConfigPresetsCoverage:
    """Tests for config_presets.py to achieve 90%+ coverage."""

    def test_convert_env_value_int(self):
        """Test convert_env_value() with integer."""
        assert convert_env_value("123") == 123

    def test_convert_env_value_float(self):
        """Test convert_env_value() with float."""
        assert convert_env_value("123.45") == 123.45

    def test_convert_env_value_bool_true(self):
        """Test convert_env_value() with boolean true."""
        assert convert_env_value("true") is True
        assert convert_env_value("True") is True

    def test_convert_env_value_bool_false(self):
        """Test convert_env_value() with boolean false."""
        assert convert_env_value("false") is False
        assert convert_env_value("False") is False

    def test_convert_env_value_string(self):
        """Test convert_env_value() with string."""
        assert convert_env_value("test") == "test"

    def test_load_env_variables(self):
        """Test load_env_variables()."""
        import os
        config_data = {}
        os.environ["EMBED_CLIENT_SERVER_HOST"] = "test_host"
        os.environ["EMBED_CLIENT_SERVER_PORT"] = "8001"
        try:
            load_env_variables(config_data, prefix="EMBED_CLIENT_")
            assert "server" in config_data
            assert config_data["server"]["host"] == "test_host"
            assert config_data["server"]["port"] == 8001
        finally:
            os.environ.pop("EMBED_CLIENT_SERVER_HOST", None)
            os.environ.pop("EMBED_CLIENT_SERVER_PORT", None)

    def test_validate_client_config(self):
        """Test validate_client_config()."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("server.host", "localhost")
        config.set("server.port", 8001)
        
        errors = validate_client_config(config)
        assert isinstance(errors, list)

    def test_create_minimal_config_dict(self):
        """Test create_minimal_config_dict()."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("server.host", "localhost")
        config.set("server.port", 8001)
        
        config_dict = create_minimal_config_dict(config)
        assert isinstance(config_dict, dict)
        assert "server" in config_dict

    def test_create_secure_config_dict(self):
        """Test create_secure_config_dict()."""
        from embed_client.config import ClientConfig
        
        config = ClientConfig()
        config.set("server.host", "localhost")
        config.set("server.port", 8001)
        config.set("ssl.enabled", True)
        
        config_dict = create_secure_config_dict(config)
        assert isinstance(config_dict, dict)
        assert "ssl" in config_dict

    def test_create_http_config_for_class(self):
        """Test create_http_config_for_class()."""
        from embed_client.config import ClientConfig
        
        # create_http_config_for_class expects a class, not an instance
        config = create_http_config_for_class(ClientConfig, host="localhost", port=8001)
        assert isinstance(config, ClientConfig)
        # Check that it's HTTP config
        assert config.get("server.host") == "localhost"

    def test_create_http_token_config_for_class(self):
        """Test create_http_token_config_for_class()."""
        from embed_client.config import ClientConfig
        
        # create_http_token_config_for_class expects a class, not an instance
        config = create_http_token_config_for_class(
            ClientConfig,
            host="localhost",
            port=8001,
            api_key="test-token"
        )
        assert isinstance(config, ClientConfig)
        assert config.get("auth.method") == "api_key"

    def test_create_https_config_for_class(self):
        """Test create_https_config_for_class()."""
        from embed_client.config import ClientConfig
        
        # create_https_config_for_class expects a class, not an instance
        config = create_https_config_for_class(ClientConfig, host="localhost", port=8443)
        assert isinstance(config, ClientConfig)
        assert config.get("ssl.enabled") is True

    def test_create_https_token_config_for_class(self):
        """Test create_https_token_config_for_class()."""
        from embed_client.config import ClientConfig
        
        # create_https_token_config_for_class expects a class, not an instance
        config = create_https_token_config_for_class(ClientConfig, host="localhost", port=8443, api_key="test-token")
        assert isinstance(config, ClientConfig)
        assert config.get("ssl.enabled") is True

    def test_create_mtls_config_for_class(self):
        """Test create_mtls_config_for_class()."""
        from embed_client.config import ClientConfig
        
        # create_mtls_config_for_class expects a class, not an instance
        config = create_mtls_config_for_class(
            ClientConfig,
            host="localhost",
            port=8443,
            cert_file="/path/to/cert.pem",
            key_file="/path/to/key.pem",
            ca_cert_file="/path/to/ca.pem"
        )
        assert isinstance(config, ClientConfig)
        assert config.get("ssl.enabled") is True


class TestSSLManagerCoverage:
    """Tests for ssl_manager.py to achieve 90%+ coverage."""

    def test_ssl_manager_error(self):
        """Test SSLManagerError."""
        error = ssl_manager.SSLManagerError("Test error", error_code=-1)
        assert str(error) == "Test error"
        assert error.error_code == -1

    def test_client_ssl_manager_init(self):
        """Test ClientSSLManager.__init__()."""
        config = {"ssl": {"enabled": True}}
        manager = ssl_manager.ClientSSLManager(config)
        assert manager.config == config

    def test_client_ssl_manager_get_ssl_config(self):
        """Test ClientSSLManager.get_ssl_config()."""
        config = {"ssl": {"enabled": True, "cert_file": "/path/to/cert.pem"}}
        manager = ssl_manager.ClientSSLManager(config)
        ssl_config = manager.get_ssl_config()
        assert isinstance(ssl_config, dict)
        assert ssl_config.get("enabled") is True

    def test_client_ssl_manager_is_ssl_enabled(self):
        """Test ClientSSLManager.is_ssl_enabled()."""
        config = {"ssl": {"enabled": True}}
        manager = ssl_manager.ClientSSLManager(config)
        assert manager.is_ssl_enabled() is True

    def test_client_ssl_manager_is_mtls_enabled(self):
        """Test ClientSSLManager.is_mtls_enabled()."""
        config = {
            "ssl": {
                "enabled": True,
                "cert_file": "/path/to/cert.pem",
                "key_file": "/path/to/key.pem",
            }
        }
        manager = ssl_manager.ClientSSLManager(config)
        assert manager.is_mtls_enabled() is True

    def test_client_ssl_manager_validate_ssl_config_disabled(self):
        """Test ClientSSLManager.validate_ssl_config() with SSL disabled."""
        config = {"ssl": {"enabled": False}}
        manager = ssl_manager.ClientSSLManager(config)
        errors = manager.validate_ssl_config()
        assert len(errors) == 0

    def test_client_ssl_manager_validate_ssl_config_missing_files(self):
        """Test ClientSSLManager.validate_ssl_config() with missing files."""
        config = {
            "ssl": {
                "enabled": True,
                "cert_file": "/nonexistent/cert.pem",
                "key_file": "/nonexistent/key.pem",
                "ca_cert_file": "/nonexistent/ca.pem",
            }
        }
        manager = ssl_manager.ClientSSLManager(config)
        errors = manager.validate_ssl_config()
        assert len(errors) > 0

    def test_client_ssl_manager_get_supported_protocols(self):
        """Test ClientSSLManager.get_supported_protocols()."""
        config = {"ssl": {"enabled": True}}
        manager = ssl_manager.ClientSSLManager(config)
        protocols = manager.get_supported_protocols()
        assert isinstance(protocols, list)
        assert "TLSv1.2" in protocols
        assert "TLSv1.3" in protocols

    def test_create_ssl_manager(self):
        """Test create_ssl_manager()."""
        config = {"ssl": {"enabled": True}}
        manager = ssl_manager.create_ssl_manager(config)
        assert isinstance(manager, ssl_manager.ClientSSLManager)

