"""
Authentication system for embed-client.

This module provides authentication configuration validation for the embed-client.
All actual authentication is handled by mcp_proxy_adapter JsonRpcClient,
which uses mcp_security_framework internally.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import base64
import logging
from typing import Any, Dict, List, Optional


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str, error_code: int = 401):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AuthResult:
    """Authentication result container."""

    def __init__(
        self,
        success: bool,
        user_id: Optional[str] = None,
        roles: Optional[List[str]] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.user_id = user_id
        self.roles = roles or []
        self.error = error


class ClientAuthManager:
    """
    Client Authentication Manager.

    This class provides authentication configuration validation for the embed-client.
    All actual authentication is handled by mcp_proxy_adapter JsonRpcClient,
    which uses mcp_security_framework internally via SSLUtils.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize authentication manager.

        Args:
            config: Authentication configuration dictionary

        Note:
            This class only validates configuration structure.
            Actual authentication is handled by mcp_proxy_adapter JsonRpcClient.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def authenticate_api_key(
        self, api_key: str, header_name: str = "X-API-Key"
    ) -> AuthResult:
        """
        Authenticate using API key.

        Note: Actual authentication is handled by mcp_proxy_adapter JsonRpcClient.
        This method is kept for compatibility but returns success.

        Args:
            api_key: API key to authenticate
            header_name: Header name for API key

        Returns:
            AuthResult with authentication status
        """
        # Authentication is handled by adapter - return success for compatibility
        return AuthResult(success=True, user_id="user", roles=[])

    def authenticate_jwt(self, token: str) -> AuthResult:
        """
        Authenticate using JWT token.

        Note: Actual authentication is handled by mcp_proxy_adapter JsonRpcClient.
        This method is kept for compatibility but returns success.

        Args:
            token: JWT token to authenticate

        Returns:
            AuthResult with authentication status
        """
        # Authentication is handled by adapter - return success for compatibility
        return AuthResult(success=True, user_id="user", roles=[])

    def authenticate_basic(self, username: str, password: str) -> AuthResult:
        """
        Authenticate using basic authentication.

        Note: Basic authentication is handled by mcp_proxy_adapter JsonRpcClient.
        This method is provided for compatibility but actual authentication
        happens at the transport level.

        Args:
            username: Username
            password: Password

        Returns:
            AuthResult with authentication status
        """
        # Basic auth is handled by adapter at transport level
        # Return success for compatibility - actual auth happens in adapter
        return AuthResult(success=True, user_id=username, roles=[])

    def authenticate_certificate(self, cert_file: str, key_file: str) -> AuthResult:
        """
        Authenticate using client certificate.

        Note: Actual authentication is handled by mcp_proxy_adapter JsonRpcClient.
        This method is kept for compatibility but returns success.

        Args:
            cert_file: Path to client certificate file
            key_file: Path to client private key file

        Returns:
            AuthResult with authentication status
        """
        # Authentication is handled by adapter - return success for compatibility
        return AuthResult(success=True, user_id="user", roles=[])

    def create_jwt_token(
        self,
        user_id: str,
        roles: Optional[List[str]] = None,
        expiry_hours: Optional[int] = None,
    ) -> str:
        """
        Create JWT token for user.

        Note: JWT token creation should be done via mcp_security_framework if needed.
        This method is kept for compatibility but raises an error.

        Args:
            user_id: User identifier
            roles: List of user roles
            expiry_hours: Token expiry in hours

        Returns:
            JWT token string

        Raises:
            AuthenticationError: JWT token creation requires mcp_security_framework
        """
        raise AuthenticationError(
            "JWT token creation requires mcp_security_framework. "
            "Use mcp_security_framework directly or let adapter handle authentication."
        )

    def get_auth_headers(self, auth_method: str, **kwargs) -> Dict[str, str]:
        """
        Get authentication headers for requests.

        Args:
            auth_method: Authentication method
            **kwargs: Additional authentication parameters

        Returns:
            Dictionary of headers
        """
        headers = {}

        if auth_method == "api_key":
            api_key = kwargs.get("api_key")
            header_name = kwargs.get("header", "X-API-Key")
            if api_key:
                headers[header_name] = api_key

        elif auth_method == "jwt":
            token = kwargs.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        elif auth_method == "basic":
            username = kwargs.get("username")
            password = kwargs.get("password")
            if username and password:
                credentials = base64.b64encode(
                    f"{username}:{password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {credentials}"

        elif auth_method == "certificate":
            # Certificate authentication is handled at SSL level
            pass

        return headers

    def validate_auth_config(self) -> List[str]:
        """
        Validate authentication configuration.

        Returns:
            List of validation errors
        """
        errors = []
        auth_config = self.config.get("auth", {})
        auth_method = auth_config.get("method", "none")

        if auth_method == "api_key":
            api_keys = auth_config.get("api_keys", {})
            if not api_keys:
                errors.append("API keys not configured for api_key authentication")

        elif auth_method == "jwt":
            jwt_config = auth_config.get("jwt", {})
            if not jwt_config.get("secret"):
                errors.append("JWT secret not configured")
            if not jwt_config.get("username"):
                errors.append("JWT username not configured")
            if not jwt_config.get("password"):
                errors.append("JWT password not configured")

        elif auth_method == "certificate":
            cert_config = auth_config.get("certificate", {})
            if not cert_config.get("cert_file"):
                errors.append("Certificate file not configured")
            if not cert_config.get("key_file"):
                errors.append("Key file not configured")

        elif auth_method == "basic":
            basic_config = auth_config.get("basic", {})
            if not basic_config.get("username"):
                errors.append("Basic auth username not configured")
            if not basic_config.get("password"):
                errors.append("Basic auth password not configured")

        return errors

    def is_auth_enabled(self) -> bool:
        """Check if authentication is enabled."""
        return self.config.get("auth", {}).get("method", "none") != "none"

    def get_auth_method(self) -> str:
        """Get current authentication method."""
        return self.config.get("auth", {}).get("method", "none")

    def get_supported_methods(self) -> List[str]:
        """Get list of supported authentication methods."""
        return ["api_key", "jwt", "certificate", "basic"]


def create_auth_manager(config: Dict[str, Any]) -> ClientAuthManager:
    """
    Create authentication manager from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        ClientAuthManager instance

    Note:
        This manager only validates configuration structure.
        Actual authentication is handled by mcp_proxy_adapter JsonRpcClient.
    """
    return ClientAuthManager(config)


def create_auth_headers(auth_method: str, **kwargs) -> Dict[str, str]:
    """
    Create authentication headers for requests.

    Args:
        auth_method: Authentication method
        **kwargs: Authentication parameters

    Returns:
        Dictionary of headers
    """
    # Create temporary auth manager for header generation
    temp_config = {"auth": {"method": auth_method}}
    auth_manager = ClientAuthManager(temp_config)
    return auth_manager.get_auth_headers(auth_method, **kwargs)
