"""
Helper functions and presets for ClientConfig.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

if TYPE_CHECKING:
    from embed_client.config import ClientConfig


def convert_env_value(value: str) -> Any:
    """Convert environment variable value to appropriate Python type."""
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


def load_env_variables(
    config_data: Dict[str, Any],
    prefix: str = "EMBED_CLIENT_",
) -> None:
    """Load configuration overrides from environment variables into config_data."""
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix) :].lower().split("_", 1)
        if len(parts) != 2:
            continue
        section, param = parts
        if section not in config_data or not isinstance(config_data[section], dict):
            config_data[section] = {}
        section_dict = config_data[section]
        section_dict[param] = convert_env_value(value)


def validate_client_config(config: "ClientConfig") -> List[str]:
    """Validate configuration and return list of human-readable error messages."""
    errors: List[str] = []

    # Validate server configuration
    host = config.get("server.host")
    port = config.get("server.port")
    if not host:
        errors.append("Server host is required")
    if not port or not isinstance(port, int) or port <= 0:
        errors.append("Server port must be a positive integer")

    # Validate authentication configuration
    auth_method = config.get("auth.method", "none")
    if auth_method == "api_key":
        if not config.get("auth.api_key.key"):
            errors.append("API key is required for api_key authentication")
    elif auth_method == "jwt":
        if not all(
            [
                config.get("auth.jwt.username"),
                config.get("auth.jwt.password"),
                config.get("auth.jwt.secret"),
            ]
        ):
            errors.append(
                "Username, password, and secret are required for JWT authentication"
            )
    elif auth_method == "certificate":
        if not all(
            [
                config.get("auth.certificate.cert_file"),
                config.get("auth.certificate.key_file"),
            ]
        ):
            errors.append(
                "Certificate and key files are required for certificate authentication"
            )
    elif auth_method == "basic":
        if not all(
            [config.get("auth.basic.username"), config.get("auth.basic.password")]
        ):
            errors.append("Username and password are required for basic authentication")

    # Validate SSL configuration
    if config.get("ssl.enabled", False):
        cert_file = config.get("ssl.cert_file")
        key_file = config.get("ssl.key_file")
        ca_cert_file = config.get("ssl.ca_cert_file")

        if cert_file and not os.path.exists(cert_file):
            errors.append(f"SSL certificate file not found: {cert_file}")
        if key_file and not os.path.exists(key_file):
            errors.append(f"SSL key file not found: {key_file}")
        if ca_cert_file and not os.path.exists(ca_cert_file):
            errors.append(f"SSL CA certificate file not found: {ca_cert_file}")

    return errors


def create_minimal_config_dict(config: "ClientConfig") -> Dict[str, Any]:
    """Create minimal configuration dictionary with only essential features."""
    minimal_config = config.get_all()

    # Disable all optional features
    minimal_config["ssl"]["enabled"] = False
    minimal_config["security"]["enabled"] = False
    minimal_config["auth"]["method"] = "none"
    minimal_config["logging"]["enabled"] = False

    return minimal_config


def create_secure_config_dict(config: "ClientConfig") -> Dict[str, Any]:
    """Create secure configuration dictionary with all security features enabled."""
    secure_config = config.get_all()

    # Enable all security features
    secure_config["ssl"]["enabled"] = True
    secure_config["security"]["enabled"] = True
    secure_config["auth"]["method"] = "certificate"
    secure_config["ssl"]["verify"] = True
    secure_config["ssl"]["check_hostname"] = True
    secure_config["ssl"]["client_cert_required"] = True

    return secure_config


def create_http_config_for_class(
    config_cls: Type["ClientConfig"],
    host: str = "localhost",
    port: int = 8001,
) -> "ClientConfig":
    """Factory helper for HTTP config without authentication."""
    config = config_cls()
    config.configure_server(host, port)
    config.configure_auth_mode("none")
    config.configure_ssl(False)
    return config


def create_http_token_config_for_class(
    config_cls: Type["ClientConfig"],
    host: str = "localhost",
    port: int = 8001,
    api_key: Optional[str] = None,
) -> "ClientConfig":
    """Factory helper for HTTP config with API key authentication."""
    config = config_cls()
    config.configure_server(host, port)
    config.configure_auth_mode("api_key", key=api_key)
    config.configure_ssl(False)
    return config


def create_https_config_for_class(
    config_cls: Type["ClientConfig"],
    host: str = "localhost",
    port: int = 8443,
    cert_file: Optional[str] = None,
    key_file: Optional[str] = None,
    ca_cert_file: Optional[str] = None,
) -> "ClientConfig":
    """Factory helper for HTTPS config without authentication."""
    config = config_cls()
    config.configure_ssl(
        True,
        cert_file=cert_file,
        key_file=key_file,
        ca_cert_file=ca_cert_file,
    )
    config.configure_server(host, port)
    config.configure_auth_mode("none")
    return config


def create_https_token_config_for_class(
    config_cls: Type["ClientConfig"],
    host: str = "localhost",
    port: int = 8443,
    api_key: Optional[str] = None,
    cert_file: Optional[str] = None,
    key_file: Optional[str] = None,
    ca_cert_file: Optional[str] = None,
) -> "ClientConfig":
    """Factory helper for HTTPS config with API key authentication."""
    config = config_cls()
    config.configure_ssl(
        True,
        cert_file=cert_file,
        key_file=key_file,
        ca_cert_file=ca_cert_file,
    )
    config.configure_server(host, port)
    config.configure_auth_mode("api_key", key=api_key)
    return config


def create_mtls_config_for_class(
    config_cls: Type["ClientConfig"],
    host: str = "localhost",
    port: int = 8443,
    cert_file: Optional[str] = None,
    key_file: Optional[str] = None,
    ca_cert_file: Optional[str] = None,
) -> "ClientConfig":
    """Factory helper for mTLS config with client certificates."""
    config = config_cls()
    config.configure_ssl(
        True,
        cert_file=cert_file,
        key_file=key_file,
        ca_cert_file=ca_cert_file,
        client_cert_required=True,
    )
    config.configure_server(host, port)
    config.configure_auth_mode(
        "certificate",
        cert_file=cert_file,
        key_file=key_file,
        ca_cert_file=ca_cert_file,
    )
    return config


__all__ = [
    "load_env_variables",
    "validate_client_config",
    "create_minimal_config_dict",
    "create_secure_config_dict",
    "create_http_config_for_class",
    "create_http_token_config_for_class",
    "create_https_config_for_class",
    "create_https_token_config_for_class",
    "create_mtls_config_for_class",
]
