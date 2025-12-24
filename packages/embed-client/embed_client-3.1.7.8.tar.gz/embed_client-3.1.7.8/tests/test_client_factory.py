"""
Tests for Client Factory

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
from unittest.mock import patch, MagicMock

from embed_client.client_factory import ClientFactory, SecurityMode


class TestSecurityMode:
    """Test security mode constants."""

    def test_security_mode_constants(self):
        """Test that security mode constants are defined correctly."""
        assert SecurityMode.HTTP == "http"
        assert SecurityMode.HTTP_TOKEN == "http_token"
        assert SecurityMode.HTTPS == "https"
        assert SecurityMode.HTTPS_TOKEN == "https_token"
        assert SecurityMode.MTLS == "mtls"
        assert SecurityMode.MTLS_ROLES == "mtls_roles"


class TestClientFactory:
    """Test ClientFactory class."""

    def test_detect_security_mode_http(self):
        """Test detection of HTTP mode."""
        mode = ClientFactory.detect_security_mode("http://localhost")
        assert mode == SecurityMode.HTTP

    def test_detect_security_mode_http_token(self):
        """Test detection of HTTP + Token mode."""
        mode = ClientFactory.detect_security_mode(
            "http://localhost", auth_method="api_key"
        )
        assert mode == SecurityMode.HTTP_TOKEN

    def test_detect_security_mode_https(self):
        """Test detection of HTTPS mode."""
        mode = ClientFactory.detect_security_mode("https://localhost")
        assert mode == SecurityMode.HTTPS

    def test_detect_security_mode_https_token(self):
        """Test detection of HTTPS + Token mode."""
        mode = ClientFactory.detect_security_mode(
            "https://localhost", auth_method="api_key"
        )
        assert mode == SecurityMode.HTTPS_TOKEN

    def test_detect_security_mode_mtls(self):
        """Test detection of mTLS mode."""
        mode = ClientFactory.detect_security_mode(
            "https://localhost", cert_file="cert.pem", key_file="key.pem"
        )
        assert mode == SecurityMode.MTLS

    def test_detect_security_mode_mtls_roles(self):
        """Test detection of mTLS + Roles mode."""
        mode = ClientFactory.detect_security_mode(
            "https://localhost",
            cert_file="cert.pem",
            key_file="key.pem",
            roles=["admin"],
        )
        assert mode == SecurityMode.MTLS_ROLES

    def test_detect_security_mode_ssl_enabled_override(self):
        """Test SSL enabled override."""
        mode = ClientFactory.detect_security_mode("http://localhost", ssl_enabled=True)
        assert mode == SecurityMode.HTTPS

    def test_detect_security_mode_ssl_disabled_override(self):
        """Test SSL disabled override."""
        mode = ClientFactory.detect_security_mode(
            "https://localhost", ssl_enabled=False
        )
        assert mode == SecurityMode.HTTP

    @patch("embed_client.client_factory.EmbeddingServiceAsyncClient")
    def test_create_client_http(self, mock_client_class):
        """Test creating HTTP client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ClientFactory.create_client("http://localhost", 8001)

        mock_client_class.assert_called_once()
        assert client == mock_client

    @patch("embed_client.client_factory.EmbeddingServiceAsyncClient")
    def test_create_client_https_token(self, mock_client_class):
        """Test creating HTTPS + Token client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ClientFactory.create_client(
            "https://localhost", 8001, auth_method="api_key", api_key="test_key"
        )

        mock_client_class.assert_called_once()
        assert client == mock_client

    @patch("embed_client.client_factory.EmbeddingServiceAsyncClient")
    def test_create_client_mtls(self, mock_client_class):
        """Test creating mTLS client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ClientFactory.create_client(
            "https://localhost", 8001, cert_file="cert.pem", key_file="key.pem"
        )

        mock_client_class.assert_called_once()
        assert client == mock_client

    def test_create_config_for_mode_http(self):
        """Test creating config for HTTP mode."""
        config = ClientFactory._create_config_for_mode(
            SecurityMode.HTTP, "http://localhost", 8001, None, False
        )

        assert config["server"]["host"] == "http://localhost"
        assert config["server"]["port"] == 8001
        assert "auth" not in config
        assert "ssl" not in config

    def test_create_config_for_mode_http_token(self):
        """Test creating config for HTTP + Token mode."""
        config = ClientFactory._create_config_for_mode(
            SecurityMode.HTTP_TOKEN,
            "http://localhost",
            8001,
            "api_key",
            False,
            api_key="test_key",
        )

        assert config["server"]["host"] == "http://localhost"
        assert config["server"]["port"] == 8001
        assert config["auth"]["method"] == "api_key"
        assert config["auth"]["api_keys"]["user"] == "test_key"
        assert "ssl" not in config

    def test_create_config_for_mode_https(self):
        """Test creating config for HTTPS mode."""
        config = ClientFactory._create_config_for_mode(
            SecurityMode.HTTPS, "https://localhost", 8001, None, True
        )

        assert config["server"]["host"] == "https://localhost"
        assert config["server"]["port"] == 8001
        assert "auth" not in config
        assert config["ssl"]["enabled"] is True

    def test_create_config_for_mode_https_token(self):
        """Test creating config for HTTPS + Token mode."""
        config = ClientFactory._create_config_for_mode(
            SecurityMode.HTTPS_TOKEN,
            "https://localhost",
            8001,
            "api_key",
            True,
            api_key="test_key",
        )

        assert config["server"]["host"] == "https://localhost"
        assert config["server"]["port"] == 8001
        assert config["auth"]["method"] == "api_key"
        assert config["auth"]["api_keys"]["user"] == "test_key"
        assert config["ssl"]["enabled"] is True

    def test_create_config_for_mode_mtls(self):
        """Test creating config for mTLS mode."""
        config = ClientFactory._create_config_for_mode(
            SecurityMode.MTLS,
            "https://localhost",
            8001,
            None,
            True,
            cert_file="cert.pem",
            key_file="key.pem",
        )

        assert config["server"]["host"] == "https://localhost"
        assert config["server"]["port"] == 8001
        assert "auth" not in config
        assert config["ssl"]["enabled"] is True
        assert config["ssl"]["cert_file"] == "cert.pem"
        assert config["ssl"]["key_file"] == "key.pem"

    def test_create_auth_config_api_key(self):
        """Test creating API key auth config."""
        config = ClientFactory._create_auth_config("api_key", api_key="test_key")

        assert config["method"] == "api_key"
        assert config["api_keys"]["user"] == "test_key"

    def test_create_auth_config_api_key_with_header(self):
        """Test creating API key auth config with custom header."""
        config = ClientFactory._create_auth_config(
            "api_key", api_key="test_key", api_key_header="X-API-Key"
        )

        assert config["method"] == "api_key"
        assert config["api_keys"]["user"] == "test_key"
        assert config["api_key_header"] == "X-API-Key"

    def test_create_auth_config_jwt(self):
        """Test creating JWT auth config."""
        config = ClientFactory._create_auth_config(
            "jwt", jwt_secret="secret", jwt_username="user", jwt_password="pass"
        )

        assert config["method"] == "jwt"
        assert config["jwt"]["secret"] == "secret"
        assert config["jwt"]["username"] == "user"
        assert config["jwt"]["password"] == "pass"

    def test_create_auth_config_basic(self):
        """Test creating Basic auth config."""
        config = ClientFactory._create_auth_config(
            "basic", username="user", password="pass"
        )

        assert config["method"] == "basic"
        assert config["basic"]["username"] == "user"
        assert config["basic"]["password"] == "pass"

    def test_create_auth_config_certificate(self):
        """Test creating Certificate auth config."""
        config = ClientFactory._create_auth_config(
            "certificate", cert_file="cert.pem", key_file="key.pem"
        )

        assert config["method"] == "certificate"
        assert config["certificate"]["cert_file"] == "cert.pem"
        assert config["certificate"]["key_file"] == "key.pem"

    @patch.dict(os.environ, {"EMBED_CLIENT_API_KEY": "env_key"})
    def test_create_auth_config_from_env(self):
        """Test creating auth config from environment variables."""
        config = ClientFactory._create_auth_config("api_key")

        assert config["method"] == "api_key"
        assert config["api_keys"]["user"] == "env_key"

    def test_create_ssl_config_basic(self):
        """Test creating basic SSL config."""
        config = ClientFactory._create_ssl_config(SecurityMode.HTTPS, True)

        assert config["enabled"] is True
        assert config["verify_mode"] == "CERT_REQUIRED"
        assert config["check_hostname"] is True
        assert config["check_expiry"] is True

    def test_create_ssl_config_with_ca_cert(self):
        """Test creating SSL config with CA certificate."""
        config = ClientFactory._create_ssl_config(
            SecurityMode.HTTPS, True, ca_cert_file="ca.pem"
        )

        assert config["enabled"] is True
        assert config["ca_cert_file"] == "ca.pem"

    def test_create_ssl_config_mtls(self):
        """Test creating SSL config for mTLS."""
        config = ClientFactory._create_ssl_config(
            SecurityMode.MTLS, True, cert_file="cert.pem", key_file="key.pem"
        )

        assert config["enabled"] is True
        assert config["cert_file"] == "cert.pem"
        assert config["key_file"] == "key.pem"

    @patch("embed_client.client_factory.EmbeddingServiceAsyncClient")
    def test_create_http_client(self, mock_client_class):
        """Test creating HTTP client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ClientFactory.create_http_client("http://localhost", 8001)

        mock_client_class.assert_called_once()
        assert client == mock_client

    @patch("embed_client.client_factory.EmbeddingServiceAsyncClient")
    def test_create_http_token_client(self, mock_client_class):
        """Test creating HTTP + Token client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ClientFactory.create_http_token_client(
            "http://localhost", 8001, "api_key", api_key="test_key"
        )

        mock_client_class.assert_called_once()
        assert client == mock_client

    @patch("embed_client.client_factory.EmbeddingServiceAsyncClient")
    def test_create_https_client(self, mock_client_class):
        """Test creating HTTPS client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ClientFactory.create_https_client("https://localhost", 8001)

        mock_client_class.assert_called_once()
        assert client == mock_client

    @patch("embed_client.client_factory.EmbeddingServiceAsyncClient")
    def test_create_https_token_client(self, mock_client_class):
        """Test creating HTTPS + Token client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ClientFactory.create_https_token_client(
            "https://localhost", 8001, "api_key", api_key="test_key"
        )

        mock_client_class.assert_called_once()
        assert client == mock_client

    @patch("embed_client.client_factory.EmbeddingServiceAsyncClient")
    def test_create_mtls_client(self, mock_client_class):
        """Test creating mTLS client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ClientFactory.create_mtls_client(
            "https://localhost", "cert.pem", "key.pem", 8001
        )

        mock_client_class.assert_called_once()
        assert client == mock_client

    @patch("embed_client.client_factory.EmbeddingServiceAsyncClient")
    def test_create_mtls_roles_client(self, mock_client_class):
        """Test creating mTLS + Roles client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ClientFactory.create_mtls_roles_client(
            "https://localhost", "cert.pem", "key.pem", 8001, roles=["admin"]
        )

        mock_client_class.assert_called_once()
        assert client == mock_client

    @patch("embed_client.client_factory.ClientConfig")
    @patch("embed_client.client_factory.EmbeddingServiceAsyncClient")
    def test_from_config_file(self, mock_client_class, mock_config_class):
        """Test creating client from config file."""
        mock_config_instance = MagicMock()
        mock_config_class.return_value = mock_config_instance
        mock_client = MagicMock()
        mock_client_class.from_config.return_value = mock_client

        client = ClientFactory.from_config_file("config.json")

        mock_config_class.assert_called_once()
        mock_config_instance.load_config_file.assert_called_once_with("config.json")
        mock_client_class.from_config.assert_called_once_with(mock_config_instance)
        assert client == mock_client

    @patch.dict(
        os.environ,
        {
            "EMBED_CLIENT_BASE_URL": "https://example.com",
            "EMBED_CLIENT_PORT": "9443",
            "EMBED_CLIENT_AUTH_METHOD": "api_key",
            "EMBED_CLIENT_API_KEY": "test_key",
        },
    )
    @patch("embed_client.client_factory.EmbeddingServiceAsyncClient")
    def test_from_environment(self, mock_client_class):
        """Test creating client from environment variables."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = ClientFactory.from_environment()

        mock_client_class.assert_called_once()
        assert client == mock_client
