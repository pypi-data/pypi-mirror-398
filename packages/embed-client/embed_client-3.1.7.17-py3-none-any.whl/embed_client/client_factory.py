"""
Client Factory for Embedding Service

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

"""

import os
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.config import ClientConfig


class SecurityMode:
    """Security mode constants."""

    HTTP = "http"
    HTTP_TOKEN = "http_token"
    HTTPS = "https"
    HTTPS_TOKEN = "https_token"
    MTLS = "mtls"
    MTLS_ROLES = "mtls_roles"


class ClientFactory:
    """
    Factory for creating EmbeddingServiceAsyncClient instances with automatic
    security mode detection and configuration.

    Supports all 6 security modes:
    1. HTTP - plain HTTP without authentication
    2. HTTP + Token - HTTP with API Key, JWT, or Basic authentication
    3. HTTPS - HTTPS with server certificate verification
    4. HTTPS + Token - HTTPS with server certificates + authentication
    5. mTLS - mutual TLS with client and server certificates
    6. mTLS + Roles - mTLS with role-based access control
    """

    @staticmethod
    def detect_security_mode(
        base_url: str,
        auth_method: Optional[str] = None,
        ssl_enabled: Optional[bool] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Automatically detect security mode based on provided parameters.

        Args:
            base_url: Server base URL
            auth_method: Authentication method (none, api_key, jwt, basic, certificate)
            ssl_enabled: Whether SSL is enabled
            cert_file: Client certificate file path
            key_file: Client private key file path
            **kwargs: Additional parameters

        Returns:
            Detected security mode string
        """
        # Parse URL to determine protocol
        parsed_url = urlparse(base_url)
        is_https = parsed_url.scheme.lower() == "https"

        # Determine SSL status
        if ssl_enabled is None:
            ssl_enabled = is_https
        else:
            ssl_enabled = bool(ssl_enabled)

        # Check for mTLS (client certificates)
        has_client_cert = bool(cert_file and key_file)

        # Check for authentication
        has_auth = auth_method and auth_method != "none"

        # Determine security mode
        if ssl_enabled and has_client_cert:
            # Check for role-based access (additional certificate attributes)
            if kwargs.get("roles") or kwargs.get("role_attributes"):
                return SecurityMode.MTLS_ROLES
            else:
                return SecurityMode.MTLS
        elif ssl_enabled and has_auth:
            return SecurityMode.HTTPS_TOKEN
        elif ssl_enabled:
            return SecurityMode.HTTPS
        elif has_auth:
            return SecurityMode.HTTP_TOKEN
        else:
            return SecurityMode.HTTP

    @staticmethod
    def create_client(
        base_url: str,
        port: int = 8001,
        auth_method: Optional[str] = None,
        ssl_enabled: Optional[bool] = None,
        **kwargs,
    ) -> EmbeddingServiceAsyncClient:
        """
        Create a client with automatic security mode detection.

        Args:
            base_url: Server base URL
            port: Server port
            auth_method: Authentication method
            ssl_enabled: Whether SSL is enabled
            **kwargs: Additional configuration parameters

        Returns:
            Configured EmbeddingServiceAsyncClient instance (always uses adapter transport)
        """
        # Detect security mode
        security_mode = ClientFactory.detect_security_mode(
            base_url, auth_method, ssl_enabled, **kwargs
        )

        # Create configuration based on detected mode
        config_dict = ClientFactory._create_config_for_mode(
            security_mode, base_url, port, auth_method, ssl_enabled, **kwargs
        )

        # Create and return client (adapter transport is always used)
        return EmbeddingServiceAsyncClient(config_dict=config_dict)

    @staticmethod
    def _create_config_for_mode(
        security_mode: str,
        base_url: str,
        port: int,
        auth_method: Optional[str],
        ssl_enabled: Optional[bool],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create configuration dictionary for specific security mode.

        Args:
            security_mode: Detected security mode
            base_url: Server base URL
            port: Server port
            auth_method: Authentication method
            ssl_enabled: Whether SSL is enabled
            **kwargs: Additional parameters

        Returns:
            Configuration dictionary
        """
        config_dict = {
            "server": {"host": base_url, "port": port},
            "client": {"timeout": kwargs.get("timeout", 30.0)},
        }

        # Configure authentication
        if security_mode in [SecurityMode.HTTP_TOKEN, SecurityMode.HTTPS_TOKEN]:
            config_dict["auth"] = ClientFactory._create_auth_config(
                auth_method, **kwargs
            )
        elif (
            security_mode in [SecurityMode.MTLS, SecurityMode.MTLS_ROLES]
            and auth_method
            and auth_method != "none"
        ):
            config_dict["auth"] = ClientFactory._create_auth_config(
                auth_method, **kwargs
            )

        # Configure SSL/TLS
        if security_mode in [
            SecurityMode.HTTPS,
            SecurityMode.HTTPS_TOKEN,
            SecurityMode.MTLS,
            SecurityMode.MTLS_ROLES,
        ]:
            config_dict["ssl"] = ClientFactory._create_ssl_config(
                security_mode, ssl_enabled, **kwargs
            )

        return config_dict

    @staticmethod
    def _create_auth_config(auth_method: Optional[str], **kwargs) -> Dict[str, Any]:
        """Create authentication configuration."""
        if not auth_method or auth_method == "none":
            return {"method": "none"}

        auth_config: Dict[str, Any] = {"method": auth_method}

        if auth_method == "api_key":
            api_key = kwargs.get("api_key") or os.environ.get("EMBED_CLIENT_API_KEY")
            if api_key:
                auth_config["api_keys"] = {"user": api_key}
                if kwargs.get("api_key_header"):
                    auth_config["api_key_header"] = kwargs["api_key_header"]

        elif auth_method == "jwt":
            jwt_secret = kwargs.get("jwt_secret") or os.environ.get(
                "EMBED_CLIENT_JWT_SECRET"
            )
            jwt_username = kwargs.get("jwt_username") or os.environ.get(
                "EMBED_CLIENT_JWT_USERNAME"
            )
            jwt_password = kwargs.get("jwt_password") or os.environ.get(
                "EMBED_CLIENT_JWT_PASSWORD"
            )

            if jwt_secret and jwt_username and jwt_password:
                auth_config["jwt"] = {
                    "secret": jwt_secret,
                    "username": jwt_username,
                    "password": jwt_password,
                }
                if kwargs.get("jwt_expiry"):
                    auth_config["jwt"]["expiry"] = kwargs["jwt_expiry"]

        elif auth_method == "basic":
            username = kwargs.get("username") or os.environ.get("EMBED_CLIENT_USERNAME")
            password = kwargs.get("password") or os.environ.get("EMBED_CLIENT_PASSWORD")

            if username and password:
                auth_config["basic"] = {"username": username, "password": password}

        elif auth_method == "certificate":
            cert_file = kwargs.get("cert_file") or os.environ.get(
                "EMBED_CLIENT_CERT_FILE"
            )
            key_file = kwargs.get("key_file") or os.environ.get("EMBED_CLIENT_KEY_FILE")

            if cert_file and key_file:
                auth_config["certificate"] = {
                    "cert_file": cert_file,
                    "key_file": key_file,
                }

        return auth_config

    @staticmethod
    def _create_ssl_config(
        security_mode: str, ssl_enabled: Optional[bool], **kwargs
    ) -> Dict[str, Any]:
        """Create SSL/TLS configuration."""
        enabled = bool(ssl_enabled)
        ssl_config: Dict[str, Any] = {
            "enabled": enabled,
            "verify_mode": kwargs.get("verify_mode", "CERT_REQUIRED"),
            "check_hostname": kwargs.get("check_hostname", True),
            "check_expiry": kwargs.get("check_expiry", True),
        }

        # Add CA certificate if provided
        ca_cert_file = kwargs.get("ca_cert_file") or os.environ.get(
            "EMBED_CLIENT_CA_CERT_FILE"
        )
        if ca_cert_file:
            ssl_config["ca_cert_file"] = ca_cert_file

        # Add client certificates for mTLS
        if security_mode in [SecurityMode.MTLS, SecurityMode.MTLS_ROLES]:
            cert_file = kwargs.get("cert_file") or os.environ.get(
                "EMBED_CLIENT_CERT_FILE"
            )
            key_file = kwargs.get("key_file") or os.environ.get("EMBED_CLIENT_KEY_FILE")

            if cert_file:
                ssl_config["cert_file"] = cert_file
            if key_file:
                ssl_config["key_file"] = key_file

        return ssl_config

    @staticmethod
    def create_http_client(
        base_url: str, port: int = 8001, **kwargs
    ) -> EmbeddingServiceAsyncClient:
        """Create HTTP client (no authentication, no SSL)."""
        return ClientFactory.create_client(
            base_url, port, auth_method="none", ssl_enabled=False, **kwargs
        )

    @staticmethod
    def create_http_token_client(
        base_url: str, port: int = 8001, auth_method: str = "api_key", **kwargs
    ) -> EmbeddingServiceAsyncClient:
        """Create HTTP client with authentication."""
        return ClientFactory.create_client(
            base_url, port, auth_method=auth_method, ssl_enabled=False, **kwargs
        )

    @staticmethod
    def create_https_client(
        base_url: str, port: int = 8001, **kwargs
    ) -> EmbeddingServiceAsyncClient:
        """Create HTTPS client (no authentication, with SSL)."""
        return ClientFactory.create_client(
            base_url, port, auth_method="none", ssl_enabled=True, **kwargs
        )

    @staticmethod
    def create_https_token_client(
        base_url: str, port: int = 8001, auth_method: str = "api_key", **kwargs
    ) -> EmbeddingServiceAsyncClient:
        """Create HTTPS client with authentication."""
        return ClientFactory.create_client(
            base_url, port, auth_method=auth_method, ssl_enabled=True, **kwargs
        )

    @staticmethod
    def create_mtls_client(
        base_url: str,
        cert_file: str,
        key_file: str,
        port: int = 8001,
        auth_method: Optional[str] = None,
        **kwargs,
    ) -> EmbeddingServiceAsyncClient:
        """Create mTLS client with client certificates."""
        return ClientFactory.create_client(
            base_url,
            port,
            auth_method=auth_method,
            ssl_enabled=True,
            cert_file=cert_file,
            key_file=key_file,
            **kwargs,
        )

    @staticmethod
    def create_mtls_roles_client(
        base_url: str,
        cert_file: str,
        key_file: str,
        port: int = 8001,
        roles: Optional[list] = None,
        role_attributes: Optional[dict] = None,
        auth_method: Optional[str] = None,
        **kwargs,
    ) -> EmbeddingServiceAsyncClient:
        """Create mTLS client with role-based access control."""
        return ClientFactory.create_client(
            base_url,
            port,
            auth_method=auth_method,
            ssl_enabled=True,
            cert_file=cert_file,
            key_file=key_file,
            roles=roles,
            role_attributes=role_attributes,
            **kwargs,
        )

    @staticmethod
    def from_config_file(config_path: str) -> EmbeddingServiceAsyncClient:
        """Create client from configuration file."""
        config = ClientConfig()
        config.load_config_file(config_path)
        return EmbeddingServiceAsyncClient.from_config(config)

    @staticmethod
    def from_environment() -> EmbeddingServiceAsyncClient:
        """Create client from environment variables."""
        base_url = os.environ.get("EMBED_CLIENT_BASE_URL", "http://localhost")
        port = int(os.environ.get("EMBED_CLIENT_PORT", "8001"))
        auth_method = os.environ.get("EMBED_CLIENT_AUTH_METHOD", "none")

        # Check if SSL should be enabled
        ssl_enabled = os.environ.get("EMBED_CLIENT_SSL_ENABLED", "").lower() in [
            "true",
            "1",
            "yes",
        ]
        if not ssl_enabled and base_url.startswith("https://"):
            ssl_enabled = True

        return ClientFactory.create_client(
            base_url, port, auth_method=auth_method, ssl_enabled=ssl_enabled
        )


from embed_client.client_factory_helpers import (  # noqa: E402  # lazy import to avoid circular dependency
    create_client,
    create_client_from_config,
    create_client_from_env,
    detect_security_mode,
)

__all__ = [
    "ClientFactory",
    "SecurityMode",
    "create_client",
    "create_client_from_config",
    "create_client_from_env",
    "detect_security_mode",
]
