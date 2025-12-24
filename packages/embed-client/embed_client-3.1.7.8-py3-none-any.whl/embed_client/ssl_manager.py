"""
SSL/TLS Manager for embed-client.

This module provides SSL/TLS configuration validation for the embed-client.
All actual SSL/TLS operations are handled by mcp_proxy_adapter JsonRpcClient,
which uses mcp_security_framework internally via SSLUtils.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import logging
import os
from typing import Any, Dict, List


class SSLManagerError(Exception):
    """Raised when SSL/TLS operations fail."""

    def __init__(self, message: str, error_code: int = -32002):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ClientSSLManager:
    """
    Client SSL/TLS Manager.

    This class provides SSL/TLS configuration validation for the embed-client.
    All actual SSL/TLS operations are handled by mcp_proxy_adapter JsonRpcClient,
    which uses mcp_security_framework internally via SSLUtils.

    This class is used only for configuration structure validation and diagnostics.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SSL/TLS manager.

        Args:
            config: SSL/TLS configuration dictionary

        Note:
            This class only validates configuration structure.
            Actual SSL/TLS is handled by mcp_proxy_adapter JsonRpcClient.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def get_ssl_config(self) -> Dict[str, Any]:
        """
        Get current SSL configuration.

        Returns:
            Dictionary with SSL configuration
        """
        return self.config.get("ssl", {})

    def is_ssl_enabled(self) -> bool:
        """
        Check if SSL/TLS is enabled.

        Returns:
            True if SSL/TLS is enabled, False otherwise
        """
        return self.config.get("ssl", {}).get("enabled", False)

    def is_mtls_enabled(self) -> bool:
        """
        Check if mTLS (mutual TLS) is enabled.

        Returns:
            True if mTLS is enabled, False otherwise
        """
        ssl_config = self.config.get("ssl", {})
        return (
            ssl_config.get("enabled", False)
            and bool(ssl_config.get("cert_file"))
            and bool(ssl_config.get("key_file"))
        )

    def validate_ssl_config(self) -> List[str]:
        """
        Validate SSL configuration.

        Returns:
            List of validation errors
        """
        errors: List[str] = []
        ssl_config = self.config.get("ssl", {})

        if not ssl_config.get("enabled", False):
            return errors  # SSL disabled, no validation needed

        # Check certificate files if mTLS is configured
        cert_file = ssl_config.get("cert_file")
        key_file = ssl_config.get("key_file")

        if cert_file and not os.path.exists(cert_file):
            errors.append(f"Certificate file not found: {cert_file}")

        if key_file and not os.path.exists(key_file):
            errors.append(f"Key file not found: {key_file}")

        # Check CA certificate if provided
        ca_cert_file = ssl_config.get("ca_cert_file")
        if ca_cert_file and not os.path.exists(ca_cert_file):
            errors.append(f"CA certificate file not found: {ca_cert_file}")

        # Certificate validation is handled by adapter via mcp_security_framework
        # We only validate file existence here

        return errors

    def get_supported_protocols(self) -> List[str]:
        """
        Get list of supported SSL/TLS protocols.

        Returns:
            List of supported protocol names
        """
        # Protocols are handled by adapter, return standard list
        return ["TLSv1.2", "TLSv1.3"]


def create_ssl_manager(config: Dict[str, Any]) -> ClientSSLManager:
    """
    Create SSL/TLS manager from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        ClientSSLManager instance

    Note:
        This manager only validates configuration structure.
        Actual SSL/TLS is handled by mcp_proxy_adapter JsonRpcClient.
    """
    return ClientSSLManager(config)
