"""
Tests for client configuration management.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import os
import tempfile
import pytest
from embed_client.config import ClientConfig


class TestClientConfig:
    """Test cases for ClientConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ClientConfig()

        assert config.get("server.host") == "localhost"
        assert config.get("server.port") == 8001
        assert config.get("auth.method") == "none"
        assert config.get("ssl.enabled") is False
        assert config.get("timeout") == 30

    def test_set_and_get(self):
        """Test setting and getting configuration values."""
        config = ClientConfig()

        config.set("server.host", "example.com")
        config.set("server.port", 9000)
        config.set("auth.method", "api_key")

        assert config.get("server.host") == "example.com"
        assert config.get("server.port") == 9000
        assert config.get("auth.method") == "api_key"

    def test_nested_set_and_get(self):
        """Test setting and getting nested configuration values."""
        config = ClientConfig()

        config.set("auth.api_key.key", "test-key-123")
        config.set("auth.api_key.header", "X-Custom-Key")

        assert config.get("auth.api_key.key") == "test-key-123"
        assert config.get("auth.api_key.header") == "X-Custom-Key"

    def test_load_from_file(self):
        """Test loading configuration from file."""
        config_data = {
            "server": {"host": "test.example.com", "port": 9000},
            "auth": {"method": "api_key", "api_key": {"key": "file-key-123"}},
            "ssl": {"enabled": True},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        try:
            config = ClientConfig.from_file(temp_file)

            assert config.get("server.host") == "test.example.com"
            assert config.get("server.port") == 9000
            assert config.get("auth.method") == "api_key"
            assert config.get("auth.api_key.key") == "file-key-123"
            assert config.get("ssl.enabled") is True
        finally:
            os.unlink(temp_file)

    def test_configure_auth_mode_api_key(self):
        """Test configuring API key authentication."""
        config = ClientConfig()

        config.configure_auth_mode("api_key", key="test-key-456", header="X-API-Key")

        assert config.get("auth.method") == "api_key"
        assert config.get("auth.api_key.key") == "test-key-456"
        assert config.get("auth.api_key.header") == "X-API-Key"

    def test_configure_auth_mode_jwt(self):
        """Test configuring JWT authentication."""
        config = ClientConfig()

        config.configure_auth_mode(
            "jwt",
            username="testuser",
            password="testpass",
            secret="testsecret",
            expiry_hours=48,
        )

        assert config.get("auth.method") == "jwt"
        assert config.get("auth.jwt.username") == "testuser"
        assert config.get("auth.jwt.password") == "testpass"
        assert config.get("auth.jwt.secret") == "testsecret"
        assert config.get("auth.jwt.expiry_hours") == 48

    def test_configure_auth_mode_certificate(self):
        """Test configuring certificate authentication."""
        config = ClientConfig()

        config.configure_auth_mode(
            "certificate",
            cert_file="/path/to/cert.crt",
            key_file="/path/to/key.key",
            ca_cert_file="/path/to/ca.crt",
        )

        assert config.get("auth.method") == "certificate"
        assert config.get("auth.certificate.enabled") is True
        assert config.get("auth.certificate.cert_file") == "/path/to/cert.crt"
        assert config.get("auth.certificate.key_file") == "/path/to/key.key"
        assert config.get("auth.certificate.ca_cert_file") == "/path/to/ca.crt"

    def test_configure_ssl(self):
        """Test configuring SSL settings."""
        config = ClientConfig()

        config.configure_ssl(
            True,
            verify=False,
            check_hostname=False,
            cert_file="/path/to/cert.crt",
            key_file="/path/to/key.key",
        )

        assert config.get("ssl.enabled") is True
        assert config.get("ssl.verify") is False
        assert config.get("ssl.check_hostname") is False
        assert config.get("ssl.cert_file") == "/path/to/cert.crt"
        assert config.get("ssl.key_file") == "/path/to/key.key"

    def test_configure_server(self):
        """Test configuring server settings."""
        config = ClientConfig()

        config.configure_server("example.com", 9000)

        assert config.get("server.host") == "example.com"
        assert config.get("server.port") == 9000
        assert config.get("server.base_url") == "http://example.com:9000"

    def test_configure_server_with_ssl(self):
        """Test configuring server settings with SSL."""
        config = ClientConfig()
        config.configure_ssl(True)
        config.configure_server("example.com", 9000)

        assert config.get("server.base_url") == "https://example.com:9000"

    def test_get_server_url(self):
        """Test getting server URL."""
        config = ClientConfig()
        config.configure_server("example.com", 9000)

        assert config.get_server_url() == "http://example.com:9000"

    def test_get_auth_method(self):
        """Test getting authentication method."""
        config = ClientConfig()
        config.configure_auth_mode("api_key")

        assert config.get_auth_method() == "api_key"

    def test_is_ssl_enabled(self):
        """Test checking if SSL is enabled."""
        config = ClientConfig()

        assert config.is_ssl_enabled() is False

        config.configure_ssl(True)
        assert config.is_ssl_enabled() is True

    def test_is_auth_enabled(self):
        """Test checking if authentication is enabled."""
        config = ClientConfig()

        assert config.is_auth_enabled() is False

        config.configure_auth_mode("api_key")
        assert config.is_auth_enabled() is True

    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        config = ClientConfig()
        config.configure_server("example.com", 9000)
        config.configure_auth_mode("api_key", key="test-key")

        errors = config.validate_config()
        assert len(errors) == 0

    def test_validate_config_missing_host(self):
        """Test configuration validation with missing host."""
        config = ClientConfig()
        config.set("server.host", "")
        config.set("server.port", 9000)

        errors = config.validate_config()
        assert "Server host is required" in errors

    def test_validate_config_invalid_port(self):
        """Test configuration validation with invalid port."""
        config = ClientConfig()
        config.set("server.host", "example.com")
        config.set("server.port", -1)

        errors = config.validate_config()
        assert "Server port must be a positive integer" in errors

    def test_validate_config_missing_api_key(self):
        """Test configuration validation with missing API key."""
        config = ClientConfig()
        config.configure_server("example.com", 9000)
        config.configure_auth_mode("api_key")

        errors = config.validate_config()
        assert "API key is required for api_key authentication" in errors

    def test_validate_config_missing_jwt_credentials(self):
        """Test configuration validation with missing JWT credentials."""
        config = ClientConfig()
        config.configure_server("example.com", 9000)
        config.configure_auth_mode("jwt")

        errors = config.validate_config()
        assert "Username, password, and secret are required for JWT authentication" in errors

    def test_validate_config_missing_certificate_files(self):
        """Test configuration validation with missing certificate files."""
        config = ClientConfig()
        config.configure_server("example.com", 9000)
        config.configure_auth_mode("certificate")

        errors = config.validate_config()
        assert "Certificate and key files are required for certificate authentication" in errors

    def test_create_http_config(self):
        """Test creating HTTP configuration."""
        config = ClientConfig.create_http_config("example.com", 9000)

        assert config.get("server.host") == "example.com"
        assert config.get("server.port") == 9000
        assert config.get("server.base_url") == "http://example.com:9000"
        assert config.get("auth.method") == "none"
        assert config.get("ssl.enabled") is False

    def test_create_http_token_config(self):
        """Test creating HTTP token configuration."""
        config = ClientConfig.create_http_token_config("example.com", 9000, "test-key")

        assert config.get("server.host") == "example.com"
        assert config.get("server.port") == 9000
        assert config.get("server.base_url") == "http://example.com:9000"
        assert config.get("auth.method") == "api_key"
        assert config.get("auth.api_key.key") == "test-key"
        assert config.get("ssl.enabled") is False

    def test_create_https_config(self):
        """Test creating HTTPS configuration."""
        config = ClientConfig.create_https_config(
            "example.com",
            9443,
            "/path/to/cert.crt",
            "/path/to/key.key",
            "/path/to/ca.crt",
        )

        assert config.get("server.host") == "example.com"
        assert config.get("server.port") == 9443
        assert config.get("server.base_url") == "https://example.com:9443"
        assert config.get("auth.method") == "none"
        assert config.get("ssl.enabled") is True
        assert config.get("ssl.cert_file") == "/path/to/cert.crt"
        assert config.get("ssl.key_file") == "/path/to/key.key"
        assert config.get("ssl.ca_cert_file") == "/path/to/ca.crt"

    def test_create_https_token_config(self):
        """Test creating HTTPS token configuration."""
        config = ClientConfig.create_https_token_config(
            "example.com",
            9443,
            "test-key",
            "/path/to/cert.crt",
            "/path/to/key.key",
            "/path/to/ca.crt",
        )

        assert config.get("server.host") == "example.com"
        assert config.get("server.port") == 9443
        assert config.get("server.base_url") == "https://example.com:9443"
        assert config.get("auth.method") == "api_key"
        assert config.get("auth.api_key.key") == "test-key"
        assert config.get("ssl.enabled") is True

    def test_create_mtls_config(self):
        """Test creating mTLS configuration."""
        config = ClientConfig.create_mtls_config(
            "example.com",
            9443,
            "/path/to/cert.crt",
            "/path/to/key.key",
            "/path/to/ca.crt",
        )

        assert config.get("server.host") == "example.com"
        assert config.get("server.port") == 9443
        assert config.get("server.base_url") == "https://example.com:9443"
        assert config.get("auth.method") == "certificate"
        assert config.get("ssl.enabled") is True
        assert config.get("ssl.client_cert_required") is True

    def test_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "server": {"host": "dict.example.com", "port": 8000},
            "auth": {"method": "api_key", "api_key": {"key": "dict-key-123"}},
        }

        config = ClientConfig.from_dict(config_dict)

        assert config.get("server.host") == "dict.example.com"
        assert config.get("server.port") == 8000
        assert config.get("auth.method") == "api_key"
        assert config.get("auth.api_key.key") == "dict-key-123"

    def test_save_config(self):
        """Test saving configuration to file."""
        config = ClientConfig()
        config.configure_server("save.example.com", 8000)
        config.configure_auth_mode("api_key", key="save-key")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            config.save(temp_file)

            # Load the saved config and verify
            with open(temp_file, "r") as f:
                saved_data = json.load(f)

            assert saved_data["server"]["host"] == "save.example.com"
            assert saved_data["server"]["port"] == 8000
            assert saved_data["auth"]["method"] == "api_key"
            assert saved_data["auth"]["api_key"]["key"] == "save-key"
        finally:
            os.unlink(temp_file)

    def test_create_minimal_config(self):
        """Test creating minimal configuration."""
        config = ClientConfig()
        minimal = config.create_minimal_config()

        assert minimal["ssl"]["enabled"] is False
        assert minimal["security"]["enabled"] is False
        assert minimal["auth"]["method"] == "none"
        assert minimal["logging"]["enabled"] is False

    def test_create_secure_config(self):
        """Test creating secure configuration."""
        config = ClientConfig()
        secure = config.create_secure_config()

        assert secure["ssl"]["enabled"] is True
        assert secure["security"]["enabled"] is True
        assert secure["auth"]["method"] == "certificate"
        assert secure["ssl"]["verify"] is True
        assert secure["ssl"]["check_hostname"] is True
        assert secure["ssl"]["client_cert_required"] is True
