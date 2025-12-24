"""
Authentication examples for embed-client.

This module provides examples of how to use the authentication system
with different authentication methods and configurations.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any
from embed_client.auth import (
    ClientAuthManager,
    create_auth_manager,
    create_auth_headers,
)


def get_api_key_auth_example() -> Dict[str, Any]:
    """
    Get example configuration for API key authentication.

    Returns:
        Configuration dictionary for API key authentication
    """
    return {
        "auth": {
            "method": "api_key",
            "api_keys": {
                "admin": "admin_key_123",
                "user": "user_key_456",
                "readonly": "readonly_key_789",
            },
        }
    }


def get_jwt_auth_example() -> Dict[str, Any]:
    """
    Get example configuration for JWT authentication.

    Returns:
        Configuration dictionary for JWT authentication
    """
    return {
        "auth": {
            "method": "jwt",
            "jwt": {
                "username": "testuser",
                "password": "testpass",
                "secret": "jwt_secret_key_123",
                "expiry_hours": 24,
            },
        }
    }


def get_basic_auth_example() -> Dict[str, Any]:
    """
    Get example configuration for basic authentication.

    Returns:
        Configuration dictionary for basic authentication
    """
    return {
        "auth": {
            "method": "basic",
            "basic": {"username": "testuser", "password": "testpass"},
        }
    }


def get_certificate_auth_example() -> Dict[str, Any]:
    """
    Get example configuration for certificate authentication.

    Returns:
        Configuration dictionary for certificate authentication
    """
    return {
        "auth": {
            "method": "certificate",
            "certificate": {
                "enabled": True,
                "cert_file": "certs/client.crt",
                "key_file": "keys/client.key",
                "ca_cert_file": "certs/ca.crt",
            },
        }
    }


def demo_api_key_authentication():
    """Demonstrate API key authentication."""
    print("=== API Key Authentication Demo ===")

    config = get_api_key_auth_example()
    auth_manager = create_auth_manager(config)

    # Test authentication
    result = auth_manager.authenticate_api_key("admin_key_123")
    print(f"Authentication result: {result.success}")
    print(f"User ID: {result.user_id}")

    # Get headers for request
    headers = auth_manager.get_auth_headers("api_key", api_key="admin_key_123")
    print(f"Request headers: {headers}")

    # Validate configuration
    errors = auth_manager.validate_auth_config()
    print(f"Configuration errors: {errors}")


def demo_jwt_authentication():
    """Demonstrate JWT authentication."""
    print("\n=== JWT Authentication Demo ===")

    config = get_jwt_auth_example()
    auth_manager = create_auth_manager(config)

    try:
        # Create JWT token
        token = auth_manager.create_jwt_token("testuser", ["admin", "user"])
        print(f"Created JWT token: {token[:50]}...")

        # Validate token
        result = auth_manager.authenticate_jwt(token)
        print(f"Token validation: {result.success}")
        print(f"User ID: {result.user_id}")
        print(f"Roles: {result.roles}")

        # Get headers for request
        headers = auth_manager.get_auth_headers("jwt", token=token)
        print(f"Request headers: {headers}")

    except Exception as e:
        print(f"JWT authentication failed: {e}")


def demo_basic_authentication():
    """Demonstrate basic authentication."""
    print("\n=== Basic Authentication Demo ===")

    config = get_basic_auth_example()
    auth_manager = create_auth_manager(config)

    # Test authentication
    result = auth_manager.authenticate_basic("testuser", "testpass")
    print(f"Authentication result: {result.success}")
    print(f"User ID: {result.user_id}")

    # Get headers for request
    headers = auth_manager.get_auth_headers(
        "basic", username="testuser", password="testpass"
    )
    print(f"Request headers: {headers}")


def demo_certificate_authentication():
    """Demonstrate certificate authentication."""
    print("\n=== Certificate Authentication Demo ===")

    config = get_certificate_auth_example()
    auth_manager = create_auth_manager(config)

    # Test authentication (will fail without real certificates)
    result = auth_manager.authenticate_certificate(
        "certs/client.crt", "keys/client.key"
    )
    print(f"Authentication result: {result.success}")
    print(f"User ID: {result.user_id}")
    print(f"Error: {result.error}")

    # Get headers for request (should be empty for certificate auth)
    headers = auth_manager.get_auth_headers("certificate")
    print(f"Request headers: {headers}")


def demo_auth_headers_creation():
    """Demonstrate creating authentication headers."""
    print("\n=== Authentication Headers Demo ===")

    # API Key headers
    headers = create_auth_headers("api_key", api_key="test_key")
    print(f"API Key headers: {headers}")

    # JWT headers
    headers = create_auth_headers("jwt", token="test_token")
    print(f"JWT headers: {headers}")

    # Basic auth headers
    headers = create_auth_headers("basic", username="user", password="pass")
    print(f"Basic auth headers: {headers}")

    # Certificate headers (should be empty)
    headers = create_auth_headers("certificate")
    print(f"Certificate headers: {headers}")


def demo_configuration_validation():
    """Demonstrate configuration validation."""
    print("\n=== Configuration Validation Demo ===")

    # Valid configuration
    valid_config = get_api_key_auth_example()
    auth_manager = create_auth_manager(valid_config)
    errors = auth_manager.validate_auth_config()
    print(f"Valid config errors: {errors}")

    # Invalid configuration
    invalid_config = {"auth": {"method": "api_key", "api_keys": {}}}  # Empty API keys
    auth_manager = create_auth_manager(invalid_config)
    errors = auth_manager.validate_auth_config()
    print(f"Invalid config errors: {errors}")


def demo_supported_methods():
    """Demonstrate getting supported authentication methods."""
    print("\n=== Supported Methods Demo ===")

    config = {"auth": {"method": "api_key"}}
    auth_manager = create_auth_manager(config)

    methods = auth_manager.get_supported_methods()
    print(f"Supported authentication methods: {methods}")

    print(f"Authentication enabled: {auth_manager.is_auth_enabled()}")
    print(f"Current auth method: {auth_manager.get_auth_method()}")


def run_all_demos():
    """Run all authentication demos."""
    print("🚀 Authentication System Examples")
    print("=" * 50)

    demo_api_key_authentication()
    demo_jwt_authentication()
    demo_basic_authentication()
    demo_certificate_authentication()
    demo_auth_headers_creation()
    demo_configuration_validation()
    demo_supported_methods()

    print("\n✅ All authentication demos completed!")


if __name__ == "__main__":
    run_all_demos()
