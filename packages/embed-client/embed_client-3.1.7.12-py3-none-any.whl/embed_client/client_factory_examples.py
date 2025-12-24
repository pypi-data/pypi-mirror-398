"""
Client Factory Examples

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

This module demonstrates how to use the ClientFactory to create clients
with different security modes.
"""

import asyncio
import os
from embed_client.client_factory import (
    ClientFactory,
    SecurityMode,
    create_client,
    create_client_from_config,
    create_client_from_env,
    detect_security_mode,
)
from embed_client.async_client import EmbeddingServiceAsyncClient


async def demonstrate_security_mode_detection():
    """Demonstrate automatic security mode detection."""
    print("=== Security Mode Detection Examples ===")

    # HTTP mode
    mode = detect_security_mode("http://localhost")
    print(f"http://localhost -> {mode}")

    # HTTP + Token mode
    mode = detect_security_mode("http://localhost", auth_method="api_key")
    print(f"http://localhost + api_key -> {mode}")

    # HTTPS mode
    mode = detect_security_mode("https://localhost")
    print(f"https://localhost -> {mode}")

    # HTTPS + Token mode
    mode = detect_security_mode("https://localhost", auth_method="api_key")
    print(f"https://localhost + api_key -> {mode}")

    # mTLS mode
    mode = detect_security_mode(
        "https://localhost", cert_file="cert.pem", key_file="key.pem"
    )
    print(f"https://localhost + client certs -> {mode}")

    # mTLS + Roles mode
    mode = detect_security_mode(
        "https://localhost", cert_file="cert.pem", key_file="key.pem", roles=["admin"]
    )
    print(f"https://localhost + client certs + roles -> {mode}")

    print()


async def demonstrate_automatic_client_creation():
    """Demonstrate automatic client creation with mode detection."""
    print("=== Automatic Client Creation Examples ===")

    # HTTP client
    client = create_client("http://localhost", 8001)
    print(f"HTTP client created: {client.base_url}:{client.port}")
    print(f"  SSL enabled: {client.is_ssl_enabled()}")
    print(f"  Authenticated: {client.is_authenticated()}")
    print()

    # HTTPS client
    client = create_client("https://localhost", 8001)
    print(f"HTTPS client created: {client.base_url}:{client.port}")
    print(f"  SSL enabled: {client.is_ssl_enabled()}")
    print(f"  Authenticated: {client.is_authenticated()}")
    print()

    # HTTP + API Key client
    client = create_client(
        "http://localhost", 8001, auth_method="api_key", api_key="test_key"
    )
    print(f"HTTP + API Key client created: {client.base_url}:{client.port}")
    print(f"  SSL enabled: {client.is_ssl_enabled()}")
    print(f"  Authenticated: {client.is_authenticated()}")
    print(f"  Auth method: {client.get_auth_method()}")
    print()

    # HTTPS + JWT client
    client = create_client(
        "https://localhost",
        8001,
        auth_method="jwt",
        jwt_secret="secret",
        jwt_username="user",
        jwt_password="pass",
    )
    print(f"HTTPS + JWT client created: {client.base_url}:{client.port}")
    print(f"  SSL enabled: {client.is_ssl_enabled()}")
    print(f"  Authenticated: {client.is_authenticated()}")
    print(f"  Auth method: {client.get_auth_method()}")
    print()

    # mTLS client
    client = create_client(
        "https://localhost",
        8001,
        cert_file="client_cert.pem",
        key_file="client_key.pem",
    )
    print(f"mTLS client created: {client.base_url}:{client.port}")
    print(f"  SSL enabled: {client.is_ssl_enabled()}")
    print(f"  mTLS enabled: {client.is_mtls_enabled()}")
    print(f"  Authenticated: {client.is_authenticated()}")
    print()


async def demonstrate_specific_client_creation():
    """Demonstrate creating clients for specific security modes."""
    print("=== Specific Client Creation Examples ===")

    # HTTP client
    client = ClientFactory.create_http_client("http://localhost", 8001)
    print(f"HTTP client: {client.base_url}:{client.port}")
    print()

    # HTTP + Token client
    client = ClientFactory.create_http_token_client(
        "http://localhost", 8001, "api_key", api_key="test_key"
    )
    print(f"HTTP + Token client: {client.base_url}:{client.port}")
    print(f"  Auth method: {client.get_auth_method()}")
    print()

    # HTTPS client
    client = ClientFactory.create_https_client("https://localhost", 8001)
    print(f"HTTPS client: {client.base_url}:{client.port}")
    print(f"  SSL enabled: {client.is_ssl_enabled()}")
    print()

    # HTTPS + Token client
    client = ClientFactory.create_https_token_client(
        "https://localhost", 8001, "basic", username="user", password="pass"
    )
    print(f"HTTPS + Token client: {client.base_url}:{client.port}")
    print(f"  SSL enabled: {client.is_ssl_enabled()}")
    print(f"  Auth method: {client.get_auth_method()}")
    print()

    # mTLS client
    client = ClientFactory.create_mtls_client(
        "https://localhost", "client_cert.pem", "client_key.pem", 8001
    )
    print(f"mTLS client: {client.base_url}:{client.port}")
    print(f"  SSL enabled: {client.is_ssl_enabled()}")
    print(f"  mTLS enabled: {client.is_mtls_enabled()}")
    print()

    # mTLS + Roles client
    client = ClientFactory.create_mtls_roles_client(
        "https://localhost",
        "client_cert.pem",
        "client_key.pem",
        8001,
        roles=["admin", "user"],
        role_attributes={"department": "IT"},
    )
    print(f"mTLS + Roles client: {client.base_url}:{client.port}")
    print(f"  SSL enabled: {client.is_ssl_enabled()}")
    print(f"  mTLS enabled: {client.is_mtls_enabled()}")
    print()


async def demonstrate_environment_based_creation():
    """Demonstrate creating clients from environment variables."""
    print("=== Environment-Based Client Creation ===")

    # Set environment variables for demonstration
    os.environ["EMBED_CLIENT_BASE_URL"] = "https://example.com"
    os.environ["EMBED_CLIENT_PORT"] = "9443"
    os.environ["EMBED_CLIENT_AUTH_METHOD"] = "api_key"
    os.environ["EMBED_CLIENT_API_KEY"] = "env_test_key"

    try:
        client = create_client_from_env()
        print(f"Client from environment: {client.base_url}:{client.port}")
        print(f"  SSL enabled: {client.is_ssl_enabled()}")
        print(f"  Authenticated: {client.is_authenticated()}")
        print(f"  Auth method: {client.get_auth_method()}")
        print()
    finally:
        # Clean up environment variables
        for key in [
            "EMBED_CLIENT_BASE_URL",
            "EMBED_CLIENT_PORT",
            "EMBED_CLIENT_AUTH_METHOD",
            "EMBED_CLIENT_API_KEY",
        ]:
            os.environ.pop(key, None)


async def demonstrate_config_file_creation():
    """Demonstrate creating clients from configuration files."""
    print("=== Configuration File Client Creation ===")

    # Create a sample configuration file
    config_content = """
{
    "server": {
        "host": "https://secure.example.com",
        "port": 9443
    },
    "auth": {
        "method": "api_key",
        "api_keys": {
            "user": "config_test_key"
        }
    },
    "ssl": {
        "enabled": true,
        "verify_mode": "CERT_REQUIRED",
        "check_hostname": true,
        "check_expiry": true
    },
    "client": {
        "timeout": 30.0
    }
}
"""

    config_file = "sample_config.json"
    try:
        with open(config_file, "w") as f:
            f.write(config_content)

        client = create_client_from_config(config_file)
        print(f"Client from config file: {client.base_url}:{client.port}")
        print(f"  SSL enabled: {client.is_ssl_enabled()}")
        print(f"  Authenticated: {client.is_authenticated()}")
        print(f"  Auth method: {client.get_auth_method()}")
        print()
    finally:
        # Clean up config file
        if os.path.exists(config_file):
            os.remove(config_file)


async def demonstrate_ssl_configuration():
    """Demonstrate SSL/TLS configuration options."""
    print("=== SSL/TLS Configuration Examples ===")

    # HTTPS with custom CA certificate
    client = create_client(
        "https://localhost",
        8001,
        ca_cert_file="custom_ca.pem",
        verify_mode="CERT_REQUIRED",
        check_hostname=True,
    )
    print(f"HTTPS with custom CA: {client.base_url}:{client.port}")
    print(f"  SSL enabled: {client.is_ssl_enabled()}")
    if client.is_ssl_enabled():
        ssl_config = client.get_ssl_config()
        print(f"  SSL config: {ssl_config}")
    print()

    # HTTPS with disabled hostname checking
    client = create_client(
        "https://localhost", 8001, verify_mode="CERT_REQUIRED", check_hostname=False
    )
    print(f"HTTPS with disabled hostname check: {client.base_url}:{client.port}")
    print(f"  SSL enabled: {client.is_ssl_enabled()}")
    if client.is_ssl_enabled():
        ssl_config = client.get_ssl_config()
        print(f"  SSL config: {ssl_config}")
    print()

    # mTLS with custom SSL settings
    client = create_client(
        "https://localhost",
        8001,
        cert_file="client_cert.pem",
        key_file="client_key.pem",
        ca_cert_file="ca_cert.pem",
        verify_mode="CERT_REQUIRED",
        check_hostname=True,
        check_expiry=True,
    )
    print(f"mTLS with custom SSL settings: {client.base_url}:{client.port}")
    print(f"  SSL enabled: {client.is_ssl_enabled()}")
    print(f"  mTLS enabled: {client.is_mtls_enabled()}")
    if client.is_ssl_enabled():
        ssl_config = client.get_ssl_config()
        print(f"  SSL config: {ssl_config}")
    print()


async def demonstrate_authentication_methods():
    """Demonstrate different authentication methods."""
    print("=== Authentication Methods Examples ===")

    # API Key authentication
    client = create_client(
        "https://localhost",
        8001,
        auth_method="api_key",
        api_key="test_api_key",
        api_key_header="X-API-Key",
    )
    print(f"API Key auth: {client.get_auth_method()}")
    if client.is_authenticated():
        headers = client.get_auth_headers()
        print(f"  Auth headers: {headers}")
    print()

    # JWT authentication
    client = create_client(
        "https://localhost",
        8001,
        auth_method="jwt",
        jwt_secret="jwt_secret_key",
        jwt_username="jwt_user",
        jwt_password="jwt_password",
        jwt_expiry=3600,
    )
    print(f"JWT auth: {client.get_auth_method()}")
    if client.is_authenticated():
        headers = client.get_auth_headers()
        print(f"  Auth headers: {headers}")
    print()

    # Basic authentication
    client = create_client(
        "https://localhost",
        8001,
        auth_method="basic",
        username="basic_user",
        password="basic_password",
    )
    print(f"Basic auth: {client.get_auth_method()}")
    if client.is_authenticated():
        headers = client.get_auth_headers()
        print(f"  Auth headers: {headers}")
    print()

    # Certificate authentication
    client = create_client(
        "https://localhost",
        8001,
        auth_method="certificate",
        cert_file="auth_cert.pem",
        key_file="auth_key.pem",
    )
    print(f"Certificate auth: {client.get_auth_method()}")
    if client.is_authenticated():
        headers = client.get_auth_headers()
        print(f"  Auth headers: {headers}")
    print()


async def main():
    """Run all demonstration examples."""
    print("Client Factory Examples")
    print("=" * 50)
    print()

    await demonstrate_security_mode_detection()
    await demonstrate_automatic_client_creation()
    await demonstrate_specific_client_creation()
    await demonstrate_environment_based_creation()
    await demonstrate_config_file_creation()
    await demonstrate_ssl_configuration()
    await demonstrate_authentication_methods()

    print("All examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
