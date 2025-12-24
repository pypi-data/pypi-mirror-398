#!/usr/bin/env python3
"""Security CLI Application for Text Vectorization.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import argparse
import asyncio
import sys

from embed_client.security_cli_core import (
    SecurityCLI,
    create_config_from_security_mode,
)

# Re-export for backward compatibility
__all__ = ["SecurityCLI", "create_config_from_security_mode", "main"]


async def main() -> int:
    """Main CLI function for security-aware vectorization."""
    parser = argparse.ArgumentParser(
        description="Security CLI Application for Text Vectorization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Security Modes:
  http              - Plain HTTP without authentication
  http_token        - HTTP with API Key authentication
  http_token_roles  - HTTP with API Key and role-based access control
  https             - HTTPS with server certificate verification
  https_token       - HTTPS with server certificates + authentication
  https_token_roles - HTTPS with server certificates + authentication + roles
  mtls              - Mutual TLS with client and server certificates
  mtls_roles        - mTLS with role-based access control

Examples:
  # HTTP without authentication
  python -m embed_client.security_cli vectorize --mode http "hello world"

  # HTTP with token authentication
  python -m embed_client.security_cli vectorize --mode http_token --api-key your-key "hello world"

  # HTTPS with server certificates
  python -m embed_client.security_cli vectorize --mode https \
    --cert-file server.crt --key-file server.key "hello world"

  # mTLS with client certificates
  python -m embed_client.security_cli vectorize --mode mtls \
    --cert-file client.crt --key-file client.key --ca-cert-file ca.crt "hello world"

  # mTLS with roles
  python -m embed_client.security_cli vectorize --mode mtls_roles \
    --cert-file client.crt --key-file client.key --ca-cert-file ca.crt "hello world"
        """,
    )

    parser.add_argument(
        "--mode",
        choices=[
            "http",
            "http_token",
            "http_token_roles",
            "https",
            "https_token",
            "https_token_roles",
            "mtls",
            "mtls_roles",
        ],
        required=True,
        help="Security mode to use",
    )

    parser.add_argument(
        "--host", default="localhost", help="Server host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8001, help="Server port (default: 8001)"
    )

    parser.add_argument(
        "--api-key", help="API key for authentication (required for token modes)"
    )

    parser.add_argument(
        "--cert-file", help="Certificate file (required for HTTPS/mTLS modes)"
    )
    parser.add_argument(
        "--key-file", help="Private key file (required for HTTPS/mTLS modes)"
    )
    parser.add_argument(
        "--ca-cert-file", help="CA certificate file (required for mTLS modes)"
    )

    parser.add_argument(
        "--format",
        choices=["json", "csv", "vectors"],
        default="json",
        help="Output format",
    )
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    vectorize_parser = subparsers.add_parser("vectorize", help="Vectorize text")
    vectorize_parser.add_argument("texts", nargs="*", help="Texts to vectorize")
    vectorize_parser.add_argument(
        "--file", "-f", help="File containing texts (one per line)"
    )

    subparsers.add_parser("health", help="Check service health")

    help_parser = subparsers.add_parser("help", help="Get help from service")
    help_parser.add_argument("--command", help="Specific command to get help for")

    subparsers.add_parser("commands", help="Get available commands")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if "token" in args.mode and not args.api_key:
        print("❌ API key required for token-based authentication modes")
        return 1

    if "https" in args.mode or "mtls" in args.mode:
        if not args.cert_file or not args.key_file:
            print("❌ Certificate and key files required for HTTPS/mTLS modes")
            return 1

    if "mtls" in args.mode and not args.ca_cert_file:
        print("❌ CA certificate file required for mTLS modes")
        return 1

    config = create_config_from_security_mode(
        args.mode,
        args.host,
        args.port,
        api_key=args.api_key,
        cert_file=args.cert_file,
        key_file=args.key_file,
        ca_cert_file=args.ca_cert_file,
    )

    cli = SecurityCLI()

    try:
        print(f"🔌 Connecting using {args.mode} mode...")
        if not await cli.connect(config):
            return 1

        if args.command == "vectorize":
            texts = list(args.texts)
            if args.file:
                with open(args.file, "r", encoding="utf-8") as f:
                    texts.extend(line.strip() for line in f if line.strip())

            if not texts:
                print("❌ No texts provided")
                return 1

            print(f"🔤 Vectorizing {len(texts)} texts using {args.mode} mode...")
            await cli.vectorize_texts(texts, args.format)

        elif args.command == "health":
            print(f"🏥 Checking service health using {args.mode} mode...")
            await cli.health_check()

        elif args.command == "help":
            print(f"❓ Getting help using {args.mode} mode...")
            await cli.get_help(args.command)

        elif args.command == "commands":
            print(f"📋 Getting commands using {args.mode} mode...")
            await cli.get_commands()

        return 0

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Error: {exc}")
        return 1
    finally:
        await cli.disconnect()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(asyncio.run(main()))
