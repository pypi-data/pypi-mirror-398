"""
Configuration examples for all security modes.

This module provides ready-to-use configuration examples for all supported
security modes and authentication methods.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional
from embed_client.config import ClientConfig


def get_http_simple_config(host: str = "localhost", port: int = 8001) -> Dict[str, Any]:
    """
    Get configuration for HTTP connection without authentication.

    Args:
        host: Server host
        port: Server port

    Returns:
        Configuration dictionary
    """
    config = ClientConfig.create_http_config(host, port)
    return config.get_all()


def get_http_token_config(
    host: str = "localhost", port: int = 8001, api_key: str = "test-token-123"
) -> Dict[str, Any]:
    """
    Get configuration for HTTP connection with API key authentication.

    Args:
        host: Server host
        port: Server port
        api_key: API key for authentication

    Returns:
        Configuration dictionary
    """
    config = ClientConfig.create_http_token_config(host, port, api_key)
    return config.get_all()


def get_https_simple_config(
    host: str = "localhost",
    port: int = 8443,
    cert_file: Optional[str] = None,
    key_file: Optional[str] = None,
    ca_cert_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get configuration for HTTPS connection without authentication.

    Args:
        host: Server host
        port: Server port
        cert_file: Client certificate file (optional)
        key_file: Client key file (optional)
        ca_cert_file: CA certificate file (optional)

    Returns:
        Configuration dictionary
    """
    config = ClientConfig.create_https_config(
        host, port, cert_file, key_file, ca_cert_file
    )
    return config.get_all()


def get_https_token_config(
    host: str = "localhost",
    port: int = 8443,
    api_key: str = "test-token-123",
    cert_file: Optional[str] = None,
    key_file: Optional[str] = None,
    ca_cert_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get configuration for HTTPS connection with API key authentication.

    Args:
        host: Server host
        port: Server port
        api_key: API key for authentication
        cert_file: Client certificate file (optional)
        key_file: Client key file (optional)
        ca_cert_file: CA certificate file (optional)

    Returns:
        Configuration dictionary
    """
    config = ClientConfig.create_https_token_config(
        host, port, api_key, cert_file, key_file, ca_cert_file
    )
    return config.get_all()


def get_mtls_config(
    host: str = "localhost",
    port: int = 8443,
    cert_file: str = "certs/client.crt",
    key_file: str = "keys/client.key",
    ca_cert_file: str = "certs/ca.crt",
) -> Dict[str, Any]:
    """
    Get configuration for mTLS connection with client certificates.

    Args:
        host: Server host
        port: Server port
        cert_file: Client certificate file
        key_file: Client key file
        ca_cert_file: CA certificate file

    Returns:
        Configuration dictionary
    """
    config = ClientConfig.create_mtls_config(
        host, port, cert_file, key_file, ca_cert_file
    )
    return config.get_all()


def get_jwt_config(
    host: str = "localhost",
    port: int = 8001,
    username: str = "user",
    password: str = "password",
    secret: str = "jwt-secret",
    expiry_hours: int = 24,
) -> Dict[str, Any]:
    """
    Get configuration for HTTP connection with JWT authentication.

    Args:
        host: Server host
        port: Server port
        username: Username for JWT
        password: Password for JWT
        secret: JWT secret key
        expiry_hours: JWT token expiry in hours

    Returns:
        Configuration dictionary
    """
    config = ClientConfig()
    config.configure_server(host, port)
    config.configure_auth_mode(
        "jwt",
        username=username,
        password=password,
        secret=secret,
        expiry_hours=expiry_hours,
    )
    return config.get_all()


def get_basic_auth_config(
    host: str = "localhost",
    port: int = 8001,
    username: str = "user",
    password: str = "password",
) -> Dict[str, Any]:
    """
    Get configuration for HTTP connection with basic authentication.

    Args:
        host: Server host
        port: Server port
        username: Username for basic auth
        password: Password for basic auth

    Returns:
        Configuration dictionary
    """
    config = ClientConfig()
    config.configure_server(host, port)
    config.configure_auth_mode("basic", username=username, password=password)
    return config.get_all()


def get_all_config_examples() -> Dict[str, Dict[str, Any]]:
    """
    Get all configuration examples.

    Returns:
        Dictionary with all configuration examples
    """
    return {
        "http_simple": get_http_simple_config(),
        "http_token": get_http_token_config(),
        "https_simple": get_https_simple_config(),
        "https_token": get_https_token_config(),
        "mtls": get_mtls_config(),
        "jwt": get_jwt_config(),
        "basic_auth": get_basic_auth_config(),
    }


def save_config_examples(output_dir: str = "configs") -> None:
    """
    Save all configuration examples to files.

    Args:
        output_dir: Output directory for configuration files
    """
    import os
    import json

    os.makedirs(output_dir, exist_ok=True)

    examples = get_all_config_examples()

    for name, config in examples.items():
        filename = os.path.join(output_dir, f"{name}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"Saved configuration: {filename}")


if __name__ == "__main__":
    # Save all configuration examples
    save_config_examples()
    print("All configuration examples saved to 'configs/' directory")
