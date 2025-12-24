"""
Example usage of EmbeddingServiceAsyncClient with all security modes and ClientFactory.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

This example shows:
- how to build configuration from CLI arguments, files, and environment variables;
- how to create clients for all security modes via `ClientFactory`;
- how to run demonstration flows in `demo mode` (security modes, detection, with_auth).

For full usage and integration details see:
- docs/client_integration_guide.md
- README.md (Vectorization methods section)
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict

from embed_client.async_client import (
    EmbeddingServiceAsyncClient,
    EmbeddingServiceConfigError,
)
from embed_client.config import ClientConfig
from embed_client.client_factory import ClientFactory, create_client
from embed_client.example_async_usage_demo import (
    run_client_examples,
    demonstrate_security_modes,
    demonstrate_automatic_detection,
    demonstrate_with_auth_method,
)


def get_params() -> Any:
    """Parse command line arguments and environment variables for client configuration."""
    parser = argparse.ArgumentParser(
        description="Embedding Service Async Client Example - All Security Modes"
    )

    # Basic connection parameters
    parser.add_argument("--base-url", "-b", help="Base URL of the embedding service")
    parser.add_argument("--port", "-p", type=int, help="Port of the embedding service")
    parser.add_argument("--config", "-c", help="Path to configuration file")

    # Client factory mode
    parser.add_argument(
        "--factory-mode",
        choices=[
            "auto",
            "http",
            "http_token",
            "https",
            "https_token",
            "mtls",
            "mtls_roles",
        ],
        default="auto",
        help="Client factory mode (auto for automatic detection)",
    )

    # Authentication parameters
    parser.add_argument(
        "--auth-method",
        choices=["none", "api_key", "jwt", "basic", "certificate"],
        default="none",
        help="Authentication method",
    )
    parser.add_argument("--api-key", help="API key for api_key authentication")
    parser.add_argument("--jwt-secret", help="JWT secret for jwt authentication")
    parser.add_argument("--jwt-username", help="JWT username for jwt authentication")
    parser.add_argument("--jwt-password", help="JWT password for jwt authentication")
    parser.add_argument("--username", help="Username for basic authentication")
    parser.add_argument("--password", help="Password for basic authentication")
    parser.add_argument(
        "--cert-file", help="Certificate file for certificate authentication"
    )
    parser.add_argument("--key-file", help="Key file for certificate authentication")

    # SSL/TLS parameters
    parser.add_argument(
        "--ssl-verify-mode",
        choices=["CERT_NONE", "CERT_OPTIONAL", "CERT_REQUIRED"],
        default="CERT_REQUIRED",
        help="SSL certificate verification mode",
    )
    parser.add_argument(
        "--ssl-check-hostname",
        action="store_true",
        default=True,
        help="Enable SSL hostname checking",
    )
    parser.add_argument(
        "--ssl-check-expiry",
        action="store_true",
        default=True,
        help="Enable SSL certificate expiry checking",
    )
    parser.add_argument(
        "--ca-cert-file", help="CA certificate file for SSL verification"
    )

    # Role-based access control (for mTLS + Roles)
    parser.add_argument(
        "--roles", help="Comma-separated list of roles for mTLS + Roles mode"
    )
    parser.add_argument(
        "--role-attributes", help="JSON string of role attributes for mTLS + Roles mode"
    )

    # Additional parameters
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="Request timeout in seconds"
    )
    parser.add_argument(
        "--demo-mode",
        action="store_true",
        help="Run in demo mode (show all security modes)",
    )

    args = parser.parse_args()

    # Store demo_mode in args for later use
    args.demo_mode = args.demo_mode

    # If demo mode is requested, return args directly
    if args.demo_mode:
        return args

    # If config file is provided, load it
    if args.config:
        try:
            config = ClientConfig()
            config.load_from_file(args.config)
            return config
        except Exception as e:
            print(f"Error loading config file {args.config}: {e}")
            sys.exit(1)

    # Otherwise, build config from arguments and environment variables
    base_url = args.base_url or os.environ.get(
        "EMBED_CLIENT_BASE_URL", "http://localhost"
    )
    port = args.port or int(os.environ.get("EMBED_CLIENT_PORT", "8001"))

    if not base_url or not port:
        print(
            "Error: base_url and port must be provided via --base-url/--port "
            "arguments or EMBED_CLIENT_BASE_URL/EMBED_CLIENT_PORT "
            "environment variables."
        )
        sys.exit(1)

    # Build configuration dictionary
    config_dict: Dict[str, Any] = {
        "server": {"host": base_url, "port": port},
        "client": {"timeout": args.timeout},
        "auth": {"method": args.auth_method},
    }

    # Add authentication configuration
    if args.auth_method == "api_key":
        api_key = args.api_key or os.environ.get("EMBED_CLIENT_API_KEY")
        if api_key:
            config_dict["auth"]["api_keys"] = {"user": api_key}
        else:
            print("Warning: API key not provided for api_key authentication")

    elif args.auth_method == "jwt":
        jwt_secret = args.jwt_secret or os.environ.get("EMBED_CLIENT_JWT_SECRET")
        jwt_username = args.jwt_username or os.environ.get("EMBED_CLIENT_JWT_USERNAME")
        jwt_password = args.jwt_password or os.environ.get("EMBED_CLIENT_JWT_PASSWORD")

        if jwt_secret and jwt_username and jwt_password:
            config_dict["auth"]["jwt"] = {
                "secret": jwt_secret,
                "username": jwt_username,
                "password": jwt_password,
            }
        else:
            print("Warning: JWT credentials not fully provided")

    elif args.auth_method == "basic":
        username = args.username or os.environ.get("EMBED_CLIENT_USERNAME")
        password = args.password or os.environ.get("EMBED_CLIENT_PASSWORD")

        if username and password:
            config_dict["auth"]["basic"] = {"username": username, "password": password}
        else:
            print("Warning: Basic auth credentials not fully provided")

    elif args.auth_method == "certificate":
        cert_file = args.cert_file or os.environ.get("EMBED_CLIENT_CERT_FILE")
        key_file = args.key_file or os.environ.get("EMBED_CLIENT_KEY_FILE")

        if cert_file and key_file:
            config_dict["auth"]["certificate"] = {
                "cert_file": cert_file,
                "key_file": key_file,
            }
        else:
            print("Warning: Certificate files not fully provided")

    # Add SSL configuration if HTTPS is used or SSL parameters are provided
    if (
        base_url.startswith("https://")
        or args.ssl_verify_mode != "CERT_REQUIRED"
        or args.ca_cert_file
    ):
        # Force check_hostname=False for CERT_NONE mode
        check_hostname = args.ssl_check_hostname
        if args.ssl_verify_mode == "CERT_NONE":
            check_hostname = False

        config_dict["ssl"] = {
            "enabled": True,
            "verify_mode": args.ssl_verify_mode,
            "check_hostname": check_hostname,
            "check_expiry": args.ssl_check_expiry,
        }

        if args.ca_cert_file:
            config_dict["ssl"]["ca_cert_file"] = args.ca_cert_file

        # Add client certificates for mTLS
        if args.cert_file:
            config_dict["ssl"]["cert_file"] = args.cert_file
        if args.key_file:
            config_dict["ssl"]["key_file"] = args.key_file

    # Add role-based access control for mTLS + Roles
    if args.roles:
        roles = [role.strip() for role in args.roles.split(",")]
        config_dict["roles"] = roles

    if args.role_attributes:
        try:
            role_attributes = json.loads(args.role_attributes)
            config_dict["role_attributes"] = role_attributes
        except json.JSONDecodeError:
            print("Warning: Invalid JSON in role_attributes")

    return config_dict


async def main():
    try:
        config = get_params()

        # Check if demo mode is requested
        if hasattr(config, "demo_mode") and config.demo_mode:
            await demonstrate_security_modes()
            await demonstrate_automatic_detection()
            await demonstrate_with_auth_method()
            return

        # Create client based on factory mode
        if isinstance(config, ClientConfig):
            # Using configuration object
            client = EmbeddingServiceAsyncClient.from_config(config)
        else:
            # Using configuration dictionary
            factory_mode = getattr(config, "factory_mode", "auto")

            if factory_mode == "auto":
                # Automatic detection
                client = create_client(
                    config["server"]["host"],
                    config["server"]["port"],
                    auth_method=config["auth"]["method"],
                    **{
                        k: v
                        for k, v in config.items()
                        if k not in ["server", "auth", "ssl", "client"]
                    },
                )
            else:
                # Specific factory method
                base_url = config["server"]["host"]
                port = config["server"]["port"]
                auth_method = config["auth"]["method"]

                if factory_mode == "http":
                    client = ClientFactory.create_http_client(base_url, port)
                elif factory_mode == "http_token":
                    client = ClientFactory.create_http_token_client(
                        base_url, port, auth_method, **config.get("auth", {})
                    )
                elif factory_mode == "https":
                    client = ClientFactory.create_https_client(base_url, port)
                elif factory_mode == "https_token":
                    client = ClientFactory.create_https_token_client(
                        base_url, port, auth_method, **config.get("auth", {})
                    )
                elif factory_mode == "mtls":
                    cert_file = config.get("ssl", {}).get(
                        "cert_file", "client_cert.pem"
                    )
                    key_file = config.get("ssl", {}).get("key_file", "client_key.pem")
                    client = ClientFactory.create_mtls_client(
                        base_url, cert_file, key_file, port
                    )
                elif factory_mode == "mtls_roles":
                    cert_file = config.get("ssl", {}).get(
                        "cert_file", "client_cert.pem"
                    )
                    key_file = config.get("ssl", {}).get("key_file", "client_key.pem")
                    roles = config.get("roles", ["admin"])
                    role_attributes = config.get("role_attributes", {})
                    client = ClientFactory.create_mtls_roles_client(
                        base_url, cert_file, key_file, port, roles, role_attributes
                    )
                else:
                    client = EmbeddingServiceAsyncClient(config_dict=config)

        print("Client configuration:")
        print(f"  Base URL: {client.base_url}")
        print(f"  Port: {client.port}")
        print(f"  Authentication: {client.get_auth_method()}")
        print(f"  Authenticated: {client.is_authenticated()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"  Auth headers: {headers}")
        print(f"  SSL enabled: {client.is_ssl_enabled()}")
        print(f"  mTLS enabled: {client.is_mtls_enabled()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"  SSL config: {ssl_config}")
            protocols = client.get_supported_ssl_protocols()
            print(f"  Supported SSL protocols: {protocols}")
        print()

        # Explicit open/close example
        print("Explicit session open/close example:")
        await client.close()
        print("Session closed explicitly (manual close example).\n")

        # Use context manager
        if isinstance(config, ClientConfig):
            async with EmbeddingServiceAsyncClient.from_config(config) as client:
                await run_client_examples(client)
        else:
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                await run_client_examples(client)

    except EmbeddingServiceConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
