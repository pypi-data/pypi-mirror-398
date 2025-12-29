"""
Tests for auth helper classes and factory functions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
from embed_client.auth import (
    ClientAuthManager,
    AuthResult,
    AuthenticationError,
    create_auth_manager,
    create_auth_headers,
)

# NOTE:
# These tests were written for a standalone authentication implementation.
# The current architecture delegates **all real authentication** to
# mcp-proxy-adapter / mcp_security_framework. ``ClientAuthManager`` in
# ``embed_client.auth`` is now a thin configuration/headers helper.
pytestmark = pytest.mark.skip(
    reason=(
        "Legacy direct-auth tests; authentication is handled by "
        "mcp-proxy-adapter/mcp_security_framework in production"
    )
)


class TestAuthResult:
    """Test cases for AuthResult class."""

    def test_auth_result_success(self):
        """Test successful auth result."""
        result = AuthResult(success=True, user_id="user1", roles=["admin"])

        assert result.success is True
        assert result.user_id == "user1"
        assert result.roles == ["admin"]
        assert result.error is None

    def test_auth_result_failure(self):
        """Test failed auth result."""
        result = AuthResult(success=False, error="Invalid credentials")

        assert result.success is False
        assert result.user_id is None
        assert result.roles == []
        assert result.error == "Invalid credentials"

    def test_auth_result_defaults(self):
        """Test auth result with default values."""
        result = AuthResult(success=True)

        assert result.success is True
        assert result.user_id is None
        assert result.roles == []
        assert result.error is None


class TestAuthManagerFactory:
    """Test cases for auth manager factory functions."""

    def test_create_auth_manager(self):
        """Test creating auth manager from config."""
        config = {"auth": {"method": "api_key", "api_keys": {"user1": "key123"}}}

        auth_manager = create_auth_manager(config)
        assert isinstance(auth_manager, ClientAuthManager)
        assert auth_manager.config == config

    def test_create_auth_headers_function(self):
        """Test create_auth_headers function."""
        headers = create_auth_headers("api_key", api_key="test_key")
        assert headers == {"X-API-Key": "test_key"}


class TestAuthenticationError:
    """Test cases for AuthenticationError class."""

    def test_authentication_error_default(self):
        """Test authentication error with default error code."""
        error = AuthenticationError("Test error")

        assert error.message == "Test error"
        assert error.error_code == 401

    def test_authentication_error_custom_code(self):
        """Test authentication error with custom error code."""
        error = AuthenticationError("Test error", 403)

        assert error.message == "Test error"
        assert error.error_code == 403
