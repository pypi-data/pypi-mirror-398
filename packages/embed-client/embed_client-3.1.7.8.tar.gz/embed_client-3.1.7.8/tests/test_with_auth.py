"""
Tests for the with_auth method of EmbeddingServiceAsyncClient.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
from embed_client.async_client import EmbeddingServiceAsyncClient


class TestWithAuth:
    """Test cases for the with_auth class method."""

    def test_with_auth_api_key_single(self):
        """Test with_auth with single API key."""
        client = EmbeddingServiceAsyncClient.with_auth("http://localhost", 8001, "api_key", api_key="test_key_123")

        assert client.base_url == "http://localhost"
        assert client.port == 8001
        assert client.get_auth_method() == "api_key"
        assert client.is_authenticated()

    def test_with_auth_api_key_dict(self):
        """Test with_auth with API keys dictionary."""
        client = EmbeddingServiceAsyncClient.with_auth(
            "http://localhost",
            8001,
            "api_key",
            api_keys={"user1": "key1", "user2": "key2"},
        )

        assert client.base_url == "http://localhost"
        assert client.port == 8001
        assert client.get_auth_method() == "api_key"
        assert client.is_authenticated()

    def test_with_auth_jwt(self):
        """Test with_auth with JWT authentication."""
        client = EmbeddingServiceAsyncClient.with_auth(
            "http://localhost",
            8001,
            "jwt",
            secret="test_secret",
            username="test_user",
            password="test_pass",
        )

        assert client.base_url == "http://localhost"
        assert client.port == 8001
        assert client.get_auth_method() == "jwt"
        assert client.is_authenticated()

    def test_with_auth_jwt_with_expiry(self):
        """Test with_auth with JWT authentication and custom expiry."""
        client = EmbeddingServiceAsyncClient.with_auth(
            "http://localhost",
            8001,
            "jwt",
            secret="test_secret",
            username="test_user",
            password="test_pass",
            expiry_hours=48,
        )

        assert client.base_url == "http://localhost"
        assert client.port == 8001
        assert client.get_auth_method() == "jwt"
        assert client.is_authenticated()

    def test_with_auth_basic(self):
        """Test with_auth with basic authentication."""
        client = EmbeddingServiceAsyncClient.with_auth(
            "http://localhost",
            8001,
            "basic",
            username="test_user",
            password="test_pass",
        )

        assert client.base_url == "http://localhost"
        assert client.port == 8001
        assert client.get_auth_method() == "basic"
        assert client.is_authenticated()

    def test_with_auth_certificate(self):
        """Test with_auth with certificate authentication."""
        client = EmbeddingServiceAsyncClient.with_auth(
            "https://localhost",
            9443,
            "certificate",
            cert_file="certs/client.crt",
            key_file="keys/client.key",
        )

        assert client.base_url == "https://localhost"
        assert client.port == 9443
        assert client.get_auth_method() == "certificate"
        assert client.is_authenticated()
        assert client.is_ssl_enabled()

    def test_with_auth_certificate_with_ssl_config(self):
        """Test with_auth with certificate authentication and SSL config."""
        client = EmbeddingServiceAsyncClient.with_auth(
            "https://localhost",
            9443,
            "certificate",
            cert_file="certs/client.crt",
            key_file="keys/client.key",
            ca_cert_file="certs/ca.crt",
            verify_mode="CERT_REQUIRED",
        )

        assert client.base_url == "https://localhost"
        assert client.port == 9443
        assert client.get_auth_method() == "certificate"
        assert client.is_authenticated()
        assert client.is_ssl_enabled()
        assert client.is_mtls_enabled()

    def test_with_auth_custom_timeout(self):
        """Test with_auth with custom timeout."""
        client = EmbeddingServiceAsyncClient.with_auth(
            "http://localhost", 8001, "api_key", api_key="test_key", timeout=60.0
        )

        assert client.timeout == 60.0

    def test_with_auth_api_key_missing_parameter(self):
        """Test with_auth with missing API key parameter."""
        with pytest.raises(ValueError, match="api_keys or api_key parameter required"):
            EmbeddingServiceAsyncClient.with_auth("http://localhost", 8001, "api_key")

    def test_with_auth_jwt_missing_secret(self):
        """Test with_auth with missing JWT secret."""
        with pytest.raises(ValueError, match="secret parameter required"):
            EmbeddingServiceAsyncClient.with_auth(
                "http://localhost",
                8001,
                "jwt",
                username="test_user",
                password="test_pass",
            )

    def test_with_auth_jwt_missing_username(self):
        """Test with_auth with missing JWT username."""
        with pytest.raises(ValueError, match="username parameter required"):
            EmbeddingServiceAsyncClient.with_auth(
                "http://localhost",
                8001,
                "jwt",
                secret="test_secret",
                password="test_pass",
            )

    def test_with_auth_jwt_missing_password(self):
        """Test with_auth with missing JWT password."""
        with pytest.raises(ValueError, match="password parameter required"):
            EmbeddingServiceAsyncClient.with_auth(
                "http://localhost",
                8001,
                "jwt",
                secret="test_secret",
                username="test_user",
            )

    def test_with_auth_basic_missing_username(self):
        """Test with_auth with missing basic username."""
        with pytest.raises(ValueError, match="username parameter required"):
            EmbeddingServiceAsyncClient.with_auth("http://localhost", 8001, "basic", password="test_pass")

    def test_with_auth_basic_missing_password(self):
        """Test with_auth with missing basic password."""
        with pytest.raises(ValueError, match="password parameter required"):
            EmbeddingServiceAsyncClient.with_auth("http://localhost", 8001, "basic", username="test_user")

    def test_with_auth_certificate_missing_cert_file(self):
        """Test with_auth with missing certificate file."""
        with pytest.raises(ValueError, match="cert_file parameter required"):
            EmbeddingServiceAsyncClient.with_auth("https://localhost", 9443, "certificate", key_file="keys/client.key")

    def test_with_auth_certificate_missing_key_file(self):
        """Test with_auth with missing key file."""
        with pytest.raises(ValueError, match="key_file parameter required"):
            EmbeddingServiceAsyncClient.with_auth(
                "https://localhost", 9443, "certificate", cert_file="certs/client.crt"
            )

    def test_with_auth_unsupported_method(self):
        """Test with_auth with unsupported authentication method."""
        with pytest.raises(ValueError, match="Unsupported authentication method"):
            EmbeddingServiceAsyncClient.with_auth("http://localhost", 8001, "unsupported_method")

    def test_with_auth_ssl_config_only(self):
        """Test with_auth with SSL configuration but no authentication."""
        client = EmbeddingServiceAsyncClient.with_auth(
            "https://localhost",
            9443,
            "api_key",
            api_key="test_key",
            ssl_enabled=True,
            verify_mode="CERT_NONE",
        )

        assert client.is_ssl_enabled()
        ssl_config = client.get_ssl_config()
        assert ssl_config["verify_mode"] == "CERT_NONE"

    def test_with_auth_https_auto_ssl(self):
        """Test with_auth with HTTPS URL automatically enabling SSL."""
        client = EmbeddingServiceAsyncClient.with_auth("https://localhost", 9443, "api_key", api_key="test_key")

        assert client.is_ssl_enabled()
        assert client.base_url == "https://localhost"

    def test_with_auth_http_no_ssl(self):
        """Test with_auth with HTTP URL not enabling SSL."""
        client = EmbeddingServiceAsyncClient.with_auth("http://localhost", 8001, "api_key", api_key="test_key")

        assert not client.is_ssl_enabled()
        assert client.base_url == "http://localhost"

    def test_with_auth_ssl_disabled_explicitly(self):
        """Test with_auth with SSL explicitly disabled."""
        client = EmbeddingServiceAsyncClient.with_auth(
            "https://localhost", 9443, "api_key", api_key="test_key", ssl_enabled=False
        )

        assert not client.is_ssl_enabled()

    def test_with_auth_mtls_configuration(self):
        """Test with_auth with mTLS configuration."""
        client = EmbeddingServiceAsyncClient.with_auth(
            "https://localhost",
            9443,
            "certificate",
            cert_file="certs/client.crt",
            key_file="keys/client.key",
            ca_cert_file="certs/ca.crt",
            check_hostname=False,
        )

        assert client.is_ssl_enabled()
        assert client.is_mtls_enabled()
        ssl_config = client.get_ssl_config()
        assert ssl_config["check_hostname"] is False
        assert "ca_cert_file" in ssl_config
