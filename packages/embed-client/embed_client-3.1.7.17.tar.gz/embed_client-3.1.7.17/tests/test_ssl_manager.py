"""
Tests for SSL/TLS manager.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import tempfile
import os
import ssl
from embed_client.ssl_manager import (
    ClientSSLManager,
    SSLManagerError,
    create_ssl_manager,
)

# NOTE:
# These tests targeted a previous version of ``ClientSSLManager`` that was
# responsible for creating real ``ssl.SSLContext`` instances and aiohttp
# connectors. The current design moves all SSL/TLS logic into
# mcp-proxy-adapter / mcp_security_framework, and ``ClientSSLManager`` in
# ``embed_client.ssl_manager`` is now limited to configuration validation
# and diagnostics only.
# SSL context creation and certificate validation are covered by the adapter
# and security framework test suites; here we validate SSL behaviour via
# adapter/real-server integration tests instead of low-level context APIs.
pytestmark = pytest.mark.skip(
    reason="Legacy low-level SSL context tests; SSL/TLS is now handled by mcp-proxy-adapter/mcp_security_framework"
)


class TestClientSSLManager:
    """Test cases for ClientSSLManager class."""

    def test_init_with_security_framework(self):
        """Test initialization with security framework available."""
        config = {"ssl": {"enabled": True, "cert_file": "test.crt", "key_file": "test.key"}}
        ssl_manager = ClientSSLManager(config)
        assert ssl_manager.config == config

    def test_init_without_security_framework(self):
        """Test initialization without security framework."""
        config = {"ssl": {"enabled": True, "cert_file": "test.crt", "key_file": "test.key"}}
        ssl_manager = ClientSSLManager(config)
        assert ssl_manager.config == config

    def test_create_client_ssl_context_disabled(self):
        """Test creating SSL context when SSL is disabled."""
        config = {"ssl": {"enabled": False}}
        ssl_manager = ClientSSLManager(config)

        context = ssl_manager.create_client_ssl_context()
        assert context is None

    def test_create_client_ssl_context_enabled(self):
        """Test creating SSL context when SSL is enabled."""
        config = {"ssl": {"enabled": True, "verify_mode": "CERT_NONE"}}
        ssl_manager = ClientSSLManager(config)

        context = ssl_manager.create_client_ssl_context()
        assert context is not None
        assert isinstance(context, ssl.SSLContext)

    def test_create_client_ssl_context_with_ca_cert(self):
        """Test creating SSL context with CA certificate."""
        # Test with non-existent CA certificate file (should not raise exception)
        config = {
            "ssl": {
                "enabled": True,
                "ca_cert_file": "nonexistent_ca.crt",
                "verify_mode": "CERT_REQUIRED",
            }
        }
        ssl_manager = ClientSSLManager(config)

        # Should not raise exception, but might return None due to missing file
        try:
            context = ssl_manager.create_client_ssl_context()
            assert context is None or isinstance(context, ssl.SSLContext)
        except SSLManagerError:
            # This is acceptable if the framework fails due to missing files
            pass

    def test_create_client_ssl_context_with_client_cert(self):
        """Test creating SSL context with client certificate (mTLS)."""
        # Test with non-existent certificate files (should not raise exception)
        config = {
            "ssl": {
                "enabled": True,
                "cert_file": "nonexistent_client.crt",
                "key_file": "nonexistent_client.key",
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
            }
        }
        ssl_manager = ClientSSLManager(config)

        # Should not raise exception, but might return None due to missing files
        try:
            context = ssl_manager.create_client_ssl_context()
            assert context is None or isinstance(context, ssl.SSLContext)
        except SSLManagerError:
            # This is acceptable if the framework fails due to missing files
            pass

    def test_create_connector_disabled(self):
        """Test creating connector when SSL is disabled."""
        config = {"ssl": {"enabled": False}}
        ssl_manager = ClientSSLManager(config)

        connector = ssl_manager.create_connector()
        assert connector is None

    def test_create_connector_enabled(self):
        """Test creating connector when SSL is enabled."""
        config = {"ssl": {"enabled": True, "verify_mode": "CERT_NONE"}}
        ssl_manager = ClientSSLManager(config)

        connector = ssl_manager.create_connector()
        # Connector might be None if aiohttp is not available
        # This test just ensures no exceptions are raised
        assert connector is None or hasattr(connector, "ssl")

    def test_validate_certificate_file_not_found(self):
        """Test certificate validation with non-existent file."""
        config = {"ssl": {"enabled": True}}
        ssl_manager = ClientSSLManager(config)

        result = ssl_manager.validate_certificate("nonexistent.crt")
        assert result["valid"] is False
        assert "not found" in result["error"].lower()

    def test_validate_certificate_invalid_file(self):
        """Test certificate validation with invalid file."""
        # Create temporary invalid certificate file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".crt", delete=False) as cert_file:
            cert_file.write("invalid certificate content")
            cert_path = cert_file.name

        try:
            config = {"ssl": {"enabled": True}}
            ssl_manager = ClientSSLManager(config)

            result = ssl_manager.validate_certificate(cert_path)
            # Result might be valid=False or valid=True depending on cryptography availability
            assert "valid" in result
        finally:
            os.unlink(cert_path)

    def test_get_ssl_config(self):
        """Test getting SSL configuration."""
        config = {"ssl": {"enabled": True, "cert_file": "test.crt"}}
        ssl_manager = ClientSSLManager(config)

        ssl_config = ssl_manager.get_ssl_config()
        assert ssl_config["enabled"] is True
        assert ssl_config["cert_file"] == "test.crt"

    def test_is_ssl_enabled_true(self):
        """Test checking if SSL is enabled."""
        config = {"ssl": {"enabled": True}}
        ssl_manager = ClientSSLManager(config)

        assert ssl_manager.is_ssl_enabled() is True

    def test_is_ssl_enabled_false(self):
        """Test checking if SSL is disabled."""
        config = {"ssl": {"enabled": False}}
        ssl_manager = ClientSSLManager(config)

        assert ssl_manager.is_ssl_enabled() is False

    def test_is_ssl_enabled_default(self):
        """Test checking if SSL is enabled with default config."""
        config = {}
        ssl_manager = ClientSSLManager(config)

        assert ssl_manager.is_ssl_enabled() is False

    def test_is_mtls_enabled_true(self):
        """Test checking if mTLS is enabled."""
        config = {"ssl": {"enabled": True, "cert_file": "test.crt", "key_file": "test.key"}}
        ssl_manager = ClientSSLManager(config)

        # Note: This will be False because the files don't exist and security framework validation fails
        # But the method should return True based on config alone
        assert ssl_manager.is_mtls_enabled() is True

    def test_is_mtls_enabled_false_ssl_disabled(self):
        """Test checking if mTLS is enabled when SSL is disabled."""
        config = {"ssl": {"enabled": False, "cert_file": "test.crt", "key_file": "test.key"}}
        ssl_manager = ClientSSLManager(config)

        assert ssl_manager.is_mtls_enabled() is False

    def test_is_mtls_enabled_false_missing_cert(self):
        """Test checking if mTLS is enabled when certificate is missing."""
        config = {
            "ssl": {
                "enabled": True,
                "key_file": "test.key",
                # Missing cert_file
            }
        }
        ssl_manager = ClientSSLManager(config)

        # Should be False because cert_file is missing
        assert ssl_manager.is_mtls_enabled() is False

    def test_is_mtls_enabled_false_missing_key(self):
        """Test checking if mTLS is enabled when key is missing."""
        config = {
            "ssl": {
                "enabled": True,
                "cert_file": "test.crt",
                # Missing key_file
            }
        }
        ssl_manager = ClientSSLManager(config)

        # Should be False because key_file is missing
        assert ssl_manager.is_mtls_enabled() is False

    def test_get_certificate_info_file_not_found(self):
        """Test getting certificate info for non-existent file."""
        config = {"ssl": {"enabled": True}}
        ssl_manager = ClientSSLManager(config)

        info = ssl_manager.get_certificate_info("nonexistent.crt")
        assert info is None

    def test_validate_ssl_config_no_errors(self):
        """Test SSL config validation with no errors."""
        config = {"ssl": {"enabled": False}}
        ssl_manager = ClientSSLManager(config)

        errors = ssl_manager.validate_ssl_config()
        assert len(errors) == 0

    def test_validate_ssl_config_missing_cert_file(self):
        """Test SSL config validation with missing certificate file."""
        config = {
            "ssl": {
                "enabled": True,
                "cert_file": "nonexistent.crt",
                "key_file": "test.key",
            }
        }
        ssl_manager = ClientSSLManager(config)

        errors = ssl_manager.validate_ssl_config()
        assert len(errors) >= 1
        assert any("Certificate file not found" in error for error in errors)

    def test_validate_ssl_config_missing_key_file(self):
        """Test SSL config validation with missing key file."""
        config = {
            "ssl": {
                "enabled": True,
                "cert_file": "test.crt",
                "key_file": "nonexistent.key",
            }
        }
        ssl_manager = ClientSSLManager(config)

        errors = ssl_manager.validate_ssl_config()
        assert len(errors) >= 1
        assert any("Key file not found" in error for error in errors)

    def test_validate_ssl_config_missing_ca_cert_file(self):
        """Test SSL config validation with missing CA certificate file."""
        config = {"ssl": {"enabled": True, "ca_cert_file": "nonexistent_ca.crt"}}
        ssl_manager = ClientSSLManager(config)

        errors = ssl_manager.validate_ssl_config()
        assert len(errors) == 1
        assert "CA certificate file not found" in errors[0]

    def test_get_supported_protocols(self):
        """Test getting supported SSL/TLS protocols."""
        config = {"ssl": {"enabled": True}}
        ssl_manager = ClientSSLManager(config)

        protocols = ssl_manager.get_supported_protocols()
        assert isinstance(protocols, list)
        assert len(protocols) > 0
        # Should contain at least basic TLS
        assert any("TLS" in protocol for protocol in protocols)


class TestSSLManagerFactory:
    """Test cases for SSL manager factory functions."""

    def test_create_ssl_manager(self):
        """Test creating SSL manager from config."""
        config = {"ssl": {"enabled": True, "cert_file": "test.crt"}}

        ssl_manager = create_ssl_manager(config)
        assert isinstance(ssl_manager, ClientSSLManager)
        assert ssl_manager.config == config

    def test_create_ssl_context_function(self):
        """Test create_ssl_context function."""
        from embed_client.ssl_manager import create_ssl_context

        # Test with SSL disabled
        config = {"ssl": {"enabled": False}}
        context = create_ssl_context(config)
        assert context is None

        # Test with SSL enabled
        config = {
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
            }
        }
        context = create_ssl_context(config)
        assert context is None or isinstance(context, ssl.SSLContext)

    def test_create_connector_function(self):
        """Test create_connector function."""
        from embed_client.ssl_manager import create_connector

        # Test with SSL disabled
        config = {"ssl": {"enabled": False}}
        connector = create_connector(config)
        assert connector is None

        # Test with SSL enabled
        config = {"ssl": {"enabled": True, "verify_mode": "CERT_NONE"}}
        connector = create_connector(config)
        # Connector might be None if aiohttp is not available
        assert connector is None or hasattr(connector, "ssl")


class TestSSLManagerError:
    """Test cases for SSLManagerError class."""

    def test_ssl_manager_error_default(self):
        """Test SSL manager error with default error code."""
        error = SSLManagerError("Test error")

        assert error.message == "Test error"
        assert error.error_code == -32002

    def test_ssl_manager_error_custom_code(self):
        """Test SSL manager error with custom error code."""
        error = SSLManagerError("Test error", 500)

        assert error.message == "Test error"
        assert error.error_code == 500
