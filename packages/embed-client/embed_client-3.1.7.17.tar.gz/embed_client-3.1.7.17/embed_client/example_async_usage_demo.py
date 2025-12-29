"""
Demonstration helpers for example_async_usage.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

from typing import Any, Dict, List

from embed_client.async_client import EmbeddingServiceError, EmbeddingServiceAsyncClient
from embed_client.client_factory import ClientFactory, detect_security_mode
from embed_client.response_parsers import extract_embeddings


async def run_client_examples(client: EmbeddingServiceAsyncClient) -> None:
    """Run example operations with the client."""
    # Check health
    try:
        health = await client.health()
        print("Service health:", health)
    except EmbeddingServiceError as exc:
        print(f"Error during health check: {exc}")
        return

    # Get OpenAPI schema
    try:
        schema = await client.get_openapi_schema()
        print(
            "OpenAPI schema version:",
            schema.get("info", {}).get("version", "unknown"),
        )
    except EmbeddingServiceError as exc:
        print(f"Error getting OpenAPI schema: {exc}")

    # Get available commands
    try:
        commands = await client.get_commands()
        print(f"Available commands: {commands}")
    except EmbeddingServiceError as exc:
        print(f"Error getting commands: {exc}")

    # Test embedding generation
    try:
        texts = [
            "Hello, world!",
            "This is a test sentence.",
            "Embedding service is working!",
        ]
        result = await client.cmd("embed", {"texts": texts})

        # Extract embeddings using shared response_parsers helper
        embeddings = extract_embeddings(result)
        print(f"Generated {len(embeddings)} embeddings")
        print(
            "First embedding dimension:",
            len(embeddings[0]) if embeddings else 0,
        )
    except EmbeddingServiceError as exc:
        print(f"Error during embedding generation: {exc}")


async def demonstrate_security_modes() -> None:
    """Demonstrate all security modes using ClientFactory."""
    print("=== Security Modes Demonstration ===")
    print("This demonstration shows how to create clients for all 6 security modes.")
    print(
        "Note: These examples create client configurations "
        "but don't connect to actual servers."
    )

    # 1. HTTP mode
    print("\n1. HTTP Mode (no authentication, no SSL):")
    print("   Use case: Development, internal networks, trusted environments")
    try:
        client = ClientFactory.create_http_client("http://localhost", 8001)
        print(f"   ✓ Created HTTP client: {client.base_url}:{client.port}")
        print(f"   ✓ SSL enabled: {client.is_ssl_enabled()}")
        print(f"   ✓ Authenticated: {client.is_authenticated()}")
        print(f"   ✓ Auth method: {client.get_auth_method()}")
        await client.close()
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ Error: {exc}")

    # 2. HTTP + Token mode
    print("\n2. HTTP + Token Mode (HTTP with API key):")
    print("   Use case: API access control, simple authentication")
    try:
        client = ClientFactory.create_http_token_client(
            "http://localhost", 8001, "api_key", api_key="demo_key"
        )
        print(f"   ✓ Created HTTP + Token client: {client.base_url}:{client.port}")
        print(f"   ✓ SSL enabled: {client.is_ssl_enabled()}")
        print(f"   ✓ Authenticated: {client.is_authenticated()}")
        print(f"   ✓ Auth method: {client.get_auth_method()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"   ✓ Auth headers: {headers}")
        await client.close()
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ Error: {exc}")

    # 3. HTTPS mode
    print("\n3. HTTPS Mode (HTTPS with server certificates):")
    print("   Use case: Secure communication, public networks")
    try:
        client = ClientFactory.create_https_client("https://localhost", 9443)
        print(f"   ✓ Created HTTPS client: {client.base_url}:{client.port}")
        print(f"   ✓ SSL enabled: {client.is_ssl_enabled()}")
        print(f"   ✓ Authenticated: {client.is_authenticated()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"   ✓ SSL config: {ssl_config}")
            protocols = client.get_supported_ssl_protocols()
            print(f"   ✓ Supported SSL protocols: {protocols}")
        await client.close()
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ Error: {exc}")

    # 4. HTTPS + Token mode
    print(
        "\n4. HTTPS + Token Mode " "(HTTPS with server certificates + authentication):"
    )
    print("   Use case: Secure API access, production environments")
    try:
        client = ClientFactory.create_https_token_client(
            "https://localhost",
            9443,
            "basic",
            username="admin",
            password="secret",
        )
        print(f"   ✓ Created HTTPS + Token client: {client.base_url}:{client.port}")
        print(f"   ✓ SSL enabled: {client.is_ssl_enabled()}")
        print(f"   ✓ Authenticated: {client.is_authenticated()}")
        print(f"   ✓ Auth method: {client.get_auth_method()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"   ✓ Auth headers: {headers}")
        await client.close()
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ Error: {exc}")

    # 5. mTLS mode
    print("\n5. mTLS Mode (mutual TLS with client and server certificates):")
    print("   Use case: High security, client certificate authentication")
    try:
        client = ClientFactory.create_mtls_client(
            "https://localhost",
            "mtls_certificates/client/embedding-service.crt",
            "mtls_certificates/client/embedding-service.key",
            8443,
        )
        print(f"   ✓ Created mTLS client: {client.base_url}:{client.port}")
        print(f"   ✓ SSL enabled: {client.is_ssl_enabled()}")
        print(f"   ✓ mTLS enabled: {client.is_mtls_enabled()}")
        print(f"   ✓ Authenticated: {client.is_authenticated()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"   ✓ SSL config: {ssl_config}")
        await client.close()
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ Error: {exc}")

    # 6. mTLS + Roles mode
    print("\n6. mTLS + Roles Mode (mTLS with role-based access control):")
    print("   Use case: Enterprise security, role-based permissions")
    try:
        client = ClientFactory.create_mtls_roles_client(
            "https://localhost",
            "mtls_certificates/client/embedding-service.crt",
            "mtls_certificates/client/embedding-service.key",
            8443,
            roles=["admin", "user"],
            role_attributes={"department": "IT"},
        )
        print(f"   ✓ Created mTLS + Roles client: {client.base_url}:{client.port}")
        print(f"   ✓ SSL enabled: {client.is_ssl_enabled()}")
        print(f"   ✓ mTLS enabled: {client.is_mtls_enabled()}")
        print(f"   ✓ Authenticated: {client.is_authenticated()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"   ✓ Auth headers: {headers}")
        await client.close()
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ Error: {exc}")

    print("\n=== Security Mode Summary ===")
    print("1. HTTP: Basic connectivity, no security")
    print("2. HTTP + Token: API key authentication over HTTP")
    print("3. HTTPS: Encrypted communication with server certificates")
    print("4. HTTPS + Token: Encrypted communication + authentication")
    print("5. mTLS: Mutual certificate authentication")
    print("6. mTLS + Roles: Mutual certificates + role-based access control")


async def demonstrate_automatic_detection() -> None:
    """Demonstrate automatic security mode detection."""
    print("\n=== Automatic Security Mode Detection ===")
    print(
        "This shows how the client automatically detects the "
        "appropriate security mode."
    )

    test_cases: List[Any] = [
        ("http://localhost", None, None, None, None, "HTTP"),
        ("http://localhost", "api_key", None, None, None, "HTTP + Token"),
        ("https://localhost", None, None, None, None, "HTTPS"),
        ("https://localhost", "api_key", None, None, None, "HTTPS + Token"),
        ("https://localhost", None, None, "cert.pem", "key.pem", "mTLS"),
        (
            "https://localhost",
            None,
            None,
            "cert.pem",
            "key.pem",
            "mTLS + Roles",
            {"roles": ["admin"]},
        ),
    ]

    for case in test_cases:
        if len(case) == 6:
            base_url, auth_method, ssl_enabled, cert_file, key_file, expected = case
            kwargs: Dict[str, Any] = {}
        else:
            (
                base_url,
                auth_method,
                ssl_enabled,
                cert_file,
                key_file,
                expected,
                kwargs,
            ) = case

        try:
            mode = detect_security_mode(
                base_url, auth_method, ssl_enabled, cert_file, key_file, **kwargs
            )
            print(
                f"  ✓ {base_url} + {auth_method or 'none'} + "
                f"{cert_file or 'no cert'} -> {mode} ({expected})"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ Error detecting mode for {base_url}: {exc}")


async def demonstrate_with_auth_method() -> None:
    """Demonstrate the with_auth method for dynamic authentication."""
    print("\n=== Dynamic Authentication with with_auth() Method ===")
    print(
        "This shows how to create clients with different authentication "
        "methods using the with_auth class method."
    )

    # Demonstrate different authentication methods
    auth_examples = [
        ("api_key", {"api_key": "dynamic_api_key"}, "API Key Authentication"),
        (
            "jwt",
            {"secret": "secret", "username": "user", "password": "pass"},
            "JWT Authentication",
        ),
        ("basic", {"username": "admin", "password": "secret"}, "Basic Authentication"),
        (
            "certificate",
            {"cert_file": "client.crt", "key_file": "client.key"},
            "Certificate Authentication",
        ),
    ]

    for auth_method, kwargs, description in auth_examples:
        try:
            print(f"\n{description}:")
            auth_client = EmbeddingServiceAsyncClient.with_auth(
                "http://localhost",
                8001,
                auth_method,
                **kwargs,
            )
            print(f"  ✓ Auth method: {auth_client.get_auth_method()}")
            print(f"  ✓ Authenticated: {auth_client.is_authenticated()}")
            if auth_client.is_authenticated():
                headers = auth_client.get_auth_headers()
                print(f"  ✓ Auth headers: {headers}")
            await auth_client.close()
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ Error with {auth_method}: {exc}")

    print("\n✓ Dynamic authentication demonstration completed.")


__all__ = [
    "run_client_examples",
    "demonstrate_security_modes",
    "demonstrate_automatic_detection",
    "demonstrate_with_auth_method",
]
