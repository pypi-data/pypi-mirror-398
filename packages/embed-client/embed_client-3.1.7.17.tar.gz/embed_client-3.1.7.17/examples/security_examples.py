#!/usr/bin/env python3
"""
Examples of using embed-client with different security configurations.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

This file demonstrates all 6 security modes supported by embed-client:
1. HTTP - plain HTTP without authentication
2. HTTP + Token - HTTP with API Key, JWT, or Basic authentication
3. HTTPS - HTTPS with server certificate verification
4. HTTPS + Token - HTTPS with server certificates + authentication
5. mTLS - mutual TLS with client and server certificates
6. mTLS + Roles - mTLS with role-based access control
"""

import asyncio
import json
import os
from typing import Dict, Any

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.config import ClientConfig
from embed_client.client_factory import (
    ClientFactory, SecurityMode, create_client, create_client_from_config,
    create_client_from_env, detect_security_mode
)


async def example_1_http_plain():
    """Example 1: HTTP - plain HTTP without authentication."""
    print("=== Example 1: HTTP - Plain HTTP without authentication ===")
    
    # Method 1: Direct client creation
    async with EmbeddingServiceAsyncClient("http://localhost", 8001) as client:
        print(f"Client: {client.base_url}:{client.port}")
        print(f"SSL enabled: {client.is_ssl_enabled()}")
        print(f"Authenticated: {client.is_authenticated()}")
        
        # Test health check
        health = await client.health()
        print(f"Health: {health}")
    
    # Method 2: Using configuration dictionary
    config_dict = {
        "server": {"host": "http://localhost", "port": 8001},
        "auth": {"method": "none"},
        "ssl": {"enabled": False}
    }
    
    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        health = await client.health()
        print(f"Health via config: {health}")
    
    # Method 3: Using ClientFactory
    client = ClientFactory.create_http_client("http://localhost", 8001)
    print(f"Factory client: {client.base_url}:{client.port}")
    await client.close()


async def example_2_http_token():
    """Example 2: HTTP + Token - HTTP with API Key authentication."""
    print("\n=== Example 2: HTTP + Token - HTTP with API Key authentication ===")
    
    # Method 1: Using with_auth class method
    async with EmbeddingServiceAsyncClient.with_auth(
        "http://localhost", 8001, "api_key", api_key="your_api_key"
    ) as client:
        print(f"Client: {client.base_url}:{client.port}")
        print(f"SSL enabled: {client.is_ssl_enabled()}")
        print(f"Authenticated: {client.is_authenticated()}")
        print(f"Auth method: {client.get_auth_method()}")
        print(f"Auth headers: {client.get_auth_headers()}")
    
    # Method 2: Using configuration dictionary
    config_dict = {
        "server": {"host": "http://localhost", "port": 8001},
        "auth": {
            "method": "api_key",
            "api_keys": {"user": "your_api_key"}
        },
        "ssl": {"enabled": False}
    }
    
    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        print(f"Auth method via config: {client.get_auth_method()}")
    
    # Method 3: Using ClientFactory
    client = ClientFactory.create_http_token_client(
        "http://localhost", 8001, "api_key", api_key="your_api_key"
    )
    print(f"Factory client auth: {client.get_auth_method()}")
    await client.close()


async def example_3_https_plain():
    """Example 3: HTTPS - HTTPS with server certificate verification."""
    print("\n=== Example 3: HTTPS - HTTPS with server certificate verification ===")
    
    # Method 1: Direct client creation with HTTPS
    config_dict = {
        "server": {"host": "https://localhost", "port": 8443},
        "auth": {"method": "none"},
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "check_expiry": True
        }
    }
    
    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        print(f"Client: {client.base_url}:{client.port}")
        print(f"SSL enabled: {client.is_ssl_enabled()}")
        print(f"Authenticated: {client.is_authenticated()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"SSL config: {ssl_config}")
            protocols = client.get_supported_ssl_protocols()
            print(f"Supported SSL protocols: {protocols}")
    
    # Method 2: Using ClientFactory
    client = ClientFactory.create_https_client("https://localhost", 8443)
    print(f"Factory HTTPS client: {client.base_url}:{client.port}")
    await client.close()


async def example_4_https_token():
    """Example 4: HTTPS + Token - HTTPS with server certificates + authentication."""
    print("\n=== Example 4: HTTPS + Token - HTTPS with server certificates + authentication ===")
    
    # Method 1: Using with_auth with HTTPS
    async with EmbeddingServiceAsyncClient.with_auth(
        "https://localhost", 8443, "basic", 
        username="admin", password="secret",
        ssl_enabled=True,
        verify_mode="CERT_REQUIRED",
        check_hostname=True
    ) as client:
        print(f"Client: {client.base_url}:{client.port}")
        print(f"SSL enabled: {client.is_ssl_enabled()}")
        print(f"Authenticated: {client.is_authenticated()}")
        print(f"Auth method: {client.get_auth_method()}")
        print(f"Auth headers: {client.get_auth_headers()}")
    
    # Method 2: Using configuration dictionary
    config_dict = {
        "server": {"host": "https://localhost", "port": 8443},
        "auth": {
            "method": "jwt",
            "jwt": {
                "secret": "your_jwt_secret",
                "username": "admin",
                "password": "secret"
            }
        },
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "check_expiry": True
        }
    }
    
    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        print(f"JWT auth method: {client.get_auth_method()}")
    
    # Method 3: Using ClientFactory
    client = ClientFactory.create_https_token_client(
        "https://localhost", 8443, "api_key", api_key="your_api_key"
    )
    print(f"Factory HTTPS+Token client: {client.get_auth_method()}")
    await client.close()


async def example_5_mtls():
    """Example 5: mTLS - mutual TLS with client and server certificates."""
    print("\n=== Example 5: mTLS - Mutual TLS with client and server certificates ===")
    
    # Method 1: Using with_auth with certificates
    async with EmbeddingServiceAsyncClient.with_auth(
        "https://localhost", 8443, "certificate",
        cert_file="mtls_certificates/client/embedding-service.crt",
        key_file="mtls_certificates/client/embedding-service.key",
        ca_cert_file="mtls_certificates/ca/ca.crt",
        ssl_enabled=True,
        verify_mode="CERT_REQUIRED",
        check_hostname=True
    ) as client:
        print(f"Client: {client.base_url}:{client.port}")
        print(f"SSL enabled: {client.is_ssl_enabled()}")
        print(f"mTLS enabled: {client.is_mtls_enabled()}")
        print(f"Authenticated: {client.is_authenticated()}")
        print(f"Auth method: {client.get_auth_method()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"SSL config: {ssl_config}")
    
    # Method 2: Using configuration dictionary
    config_dict = {
        "server": {"host": "https://localhost", "port": 8443},
        "auth": {
            "method": "certificate",
            "certificate": {
                "cert_file": "mtls_certificates/client/embedding-service.crt",
                "key_file": "mtls_certificates/client/embedding-service.key",
                "ca_cert_file": "mtls_certificates/ca/ca.crt"
            }
        },
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "check_expiry": True,
            "cert_file": "mtls_certificates/client/embedding-service.crt",
            "key_file": "mtls_certificates/client/embedding-service.key",
            "ca_cert_file": "mtls_certificates/ca/ca.crt"
        }
    }
    
    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        print(f"mTLS auth method: {client.get_auth_method()}")
        print(f"mTLS enabled: {client.is_mtls_enabled()}")
    
    # Method 3: Using ClientFactory
    client = ClientFactory.create_mtls_client(
        "https://localhost", 
        "mtls_certificates/client/embedding-service.crt",
        "mtls_certificates/client/embedding-service.key",
        8443
    )
    print(f"Factory mTLS client: {client.is_mtls_enabled()}")
    await client.close()


async def example_6_mtls_roles():
    """Example 6: mTLS + Roles - mTLS with role-based access control."""
    print("\n=== Example 6: mTLS + Roles - mTLS with role-based access control ===")
    
    # Method 1: Using configuration dictionary with roles
    config_dict = {
        "server": {"host": "https://localhost", "port": 8443},
        "auth": {
            "method": "certificate",
            "certificate": {
                "cert_file": "mtls_certificates/client/embedding-service.crt",
                "key_file": "mtls_certificates/client/embedding-service.key",
                "ca_cert_file": "mtls_certificates/ca/ca.crt"
            }
        },
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "check_expiry": True,
            "cert_file": "mtls_certificates/client/embedding-service.crt",
            "key_file": "mtls_certificates/client/embedding-service.key",
            "ca_cert_file": "mtls_certificates/ca/ca.crt"
        },
        "roles": ["admin", "user", "embedding-service"],
        "role_attributes": {
            "department": "IT",
            "service": "embedding",
            "permissions": ["read", "write", "embed"]
        }
    }
    
    async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
        print(f"Client: {client.base_url}:{client.port}")
        print(f"SSL enabled: {client.is_ssl_enabled()}")
        print(f"mTLS enabled: {client.is_mtls_enabled()}")
        print(f"Authenticated: {client.is_authenticated()}")
        print(f"Auth method: {client.get_auth_method()}")
    
    # Method 2: Using ClientFactory with roles
    client = ClientFactory.create_mtls_roles_client(
        "https://localhost",
        "mtls_certificates/client/embedding-service.crt",
        "mtls_certificates/client/embedding-service.key",
        8443,
        roles=["admin", "user"],
        role_attributes={"department": "IT"}
    )
    print(f"Factory mTLS+Roles client: {client.is_mtls_enabled()}")
    await client.close()


async def example_automatic_detection():
    """Example: Automatic security mode detection."""
    print("\n=== Example: Automatic Security Mode Detection ===")
    
    test_cases = [
        ("http://localhost", None, None, None, None, "HTTP"),
        ("http://localhost", "api_key", None, None, None, "HTTP + Token"),
        ("https://localhost", None, None, None, None, "HTTPS"),
        ("https://localhost", "api_key", None, None, None, "HTTPS + Token"),
        ("https://localhost", None, None, "cert.pem", "key.pem", "mTLS"),
        ("https://localhost", None, None, "cert.pem", "key.pem", "mTLS + Roles", {"roles": ["admin"]}),
    ]
    
    for case in test_cases:
        if len(case) == 6:
            base_url, auth_method, ssl_enabled, cert_file, key_file, expected = case
            kwargs = {}
        else:
            base_url, auth_method, ssl_enabled, cert_file, key_file, expected, kwargs = case
        
        try:
            mode = detect_security_mode(base_url, auth_method, ssl_enabled, cert_file, key_file, **kwargs)
            print(f"  {base_url} + {auth_method or 'none'} + {cert_file or 'no cert'} -> {mode} ({expected})")
        except Exception as e:
            print(f"  Error detecting mode for {base_url}: {e}")


async def example_configuration_files():
    """Example: Using configuration files."""
    print("\n=== Example: Using Configuration Files ===")
    
    # Create sample configuration files
    configs = {
        "http_simple.json": {
            "server": {"host": "http://localhost", "port": 8001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False}
        },
        "https_token.json": {
            "server": {"host": "https://localhost", "port": 8443},
            "auth": {
                "method": "api_key",
                "api_keys": {"user": "your_api_key"}
            },
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_REQUIRED",
                "check_hostname": True
            }
        },
        "mtls_roles.json": {
            "server": {"host": "https://localhost", "port": 8443},
            "auth": {
                "method": "certificate",
                "certificate": {
                    "cert_file": "mtls_certificates/client/embedding-service.crt",
                    "key_file": "mtls_certificates/client/embedding-service.key",
                    "ca_cert_file": "mtls_certificates/ca/ca.crt"
                }
            },
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_REQUIRED",
                "check_hostname": True,
                "cert_file": "mtls_certificates/client/embedding-service.crt",
                "key_file": "mtls_certificates/client/embedding-service.key",
                "ca_cert_file": "mtls_certificates/ca/ca.crt"
            },
            "roles": ["admin", "user"],
            "role_attributes": {"department": "IT"}
        }
    }
    
    # Create config directory if it doesn't exist
    os.makedirs("examples/configs", exist_ok=True)
    
    # Save configuration files
    for filename, config in configs.items():
        filepath = f"examples/configs/{filename}"
        with open(filepath, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Created: {filepath}")
    
    # Example: Load configuration from file
    try:
        config = ClientConfig()
        config.load_config_file("examples/configs/http_simple.json")
        
        async with EmbeddingServiceAsyncClient.from_config(config) as client:
            print(f"Loaded from file: {client.base_url}:{client.port}")
            print(f"Auth method: {client.get_auth_method()}")
    except Exception as e:
        print(f"Error loading config file: {e}")


async def example_environment_variables():
    """Example: Using environment variables."""
    print("\n=== Example: Using Environment Variables ===")
    
    # Set environment variables (in real usage, these would be set externally)
    env_vars = {
        "EMBED_CLIENT_BASE_URL": "http://localhost",
        "EMBED_CLIENT_PORT": "8001",
        "EMBED_CLIENT_AUTH_METHOD": "api_key",
        "EMBED_CLIENT_API_KEY": "your_api_key"
    }
    
    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"Set {key}={value}")
    
    # Create client from environment variables
    try:
        client = create_client_from_env()
        print(f"Client from env: {client.base_url}:{client.port}")
        print(f"Auth method: {client.get_auth_method()}")
        await client.close()
    except Exception as e:
        print(f"Error creating client from env: {e}")
    
    # Clean up environment variables
    for key in env_vars.keys():
        if key in os.environ:
            del os.environ[key]


async def example_embedding_generation():
    """Example: Generate embeddings with different security modes."""
    print("\n=== Example: Generate Embeddings with Different Security Modes ===")
    
    texts = ["Hello, world!", "This is a test sentence.", "Embedding service is working!"]
    
    # HTTP mode
    try:
        async with EmbeddingServiceAsyncClient("http://localhost", 8001) as client:
            result = await client.cmd("embed", {"texts": texts})
            if result.get("success"):
                print(f"HTTP mode: Generated {len(result.get('result', {}).get('data', []))} embeddings")
            else:
                print(f"HTTP mode: Failed - {result.get('error')}")
    except Exception as e:
        print(f"HTTP mode error: {e}")
    
    # API Key mode
    try:
        async with EmbeddingServiceAsyncClient.with_auth(
            "http://localhost", 8001, "api_key", api_key="your_api_key"
        ) as client:
            result = await client.cmd("embed", {"texts": texts})
            if result.get("success"):
                print(f"API Key mode: Generated {len(result.get('result', {}).get('data', []))} embeddings")
            else:
                print(f"API Key mode: Failed - {result.get('error')}")
    except Exception as e:
        print(f"API Key mode error: {e}")


async def main():
    """Run all examples."""
    print("🚀 embed-client Security Examples")
    print("=" * 50)
    
    try:
        await example_1_http_plain()
        await example_2_http_token()
        await example_3_https_plain()
        await example_4_https_token()
        await example_5_mtls()
        await example_6_mtls_roles()
        await example_automatic_detection()
        await example_configuration_files()
        await example_environment_variables()
        await example_embedding_generation()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
