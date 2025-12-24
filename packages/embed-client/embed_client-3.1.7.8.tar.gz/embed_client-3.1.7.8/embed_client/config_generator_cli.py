"""
CLI entry point for the embed-client configuration generator.

This module provides the command-line interface for generating configuration
files for all supported security modes using `ClientConfigGenerator`.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import argparse
from pathlib import Path

from embed_client.config_generator import ClientConfigGenerator


def main() -> None:
    """CLI entry point for the configuration generator."""
    parser = argparse.ArgumentParser(description="Generate embed-client configurations")
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
            "all",
        ],
        default="all",
        help="Security mode to generate",
    )
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8001, help="Server port")
    parser.add_argument("--output", help="Output file path (for single mode)")
    parser.add_argument(
        "--output-dir", default="./configs", help="Output directory (for all modes)"
    )
    parser.add_argument("--cert-file", help="Client certificate file (for HTTPS/mTLS)")
    parser.add_argument("--key-file", help="Client key file (for HTTPS/mTLS)")
    parser.add_argument("--ca-cert-file", help="CA certificate file (for HTTPS/mTLS)")
    parser.add_argument("--api-key", help="API key for token modes")

    args = parser.parse_args()

    generator = ClientConfigGenerator()
    output_dir = Path(args.output_dir) if args.output_dir else None

    if args.mode == "all":
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        configs = generator.generate_all_configs(
            host=args.host,
            port=args.port,
            output_dir=output_dir,
            cert_file=args.cert_file,
            key_file=args.key_file,
            ca_cert_file=args.ca_cert_file,
        )
        print(f"✅ Generated {len(configs)} configurations in {output_dir}")
    else:
        output_path = Path(args.output) if args.output else output_dir / f"{args.mode}.json"  # type: ignore[operator]
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)

        if args.mode == "http":
            generator.generate_http_config(
                host=args.host, port=args.port, output_path=output_path
            )
        elif args.mode == "http_token":
            generator.generate_http_token_config(
                host=args.host,
                port=args.port,
                api_key=args.api_key,
                output_path=output_path,
            )
        elif args.mode == "http_token_roles":
            generator.generate_http_token_roles_config(
                host=args.host,
                port=args.port,
                api_key=args.api_key,
                output_path=output_path,
            )
        elif args.mode == "https":
            generator.generate_https_config(
                host=args.host,
                port=args.port,
                cert_file=args.cert_file,
                key_file=args.key_file,
                ca_cert_file=args.ca_cert_file,
                output_path=output_path,
            )
        elif args.mode == "https_token":
            generator.generate_https_token_config(
                host=args.host,
                port=args.port,
                api_key=args.api_key,
                cert_file=args.cert_file,
                key_file=args.key_file,
                ca_cert_file=args.ca_cert_file,
                output_path=output_path,
            )
        elif args.mode == "https_token_roles":
            generator.generate_https_token_roles_config(
                host=args.host,
                port=args.port,
                api_key=args.api_key,
                cert_file=args.cert_file,
                key_file=args.key_file,
                ca_cert_file=args.ca_cert_file,
                output_path=output_path,
            )
        elif args.mode == "mtls":
            generator.generate_mtls_config(
                host=args.host,
                port=args.port,
                cert_file=args.cert_file,
                key_file=args.key_file,
                ca_cert_file=args.ca_cert_file,
                output_path=output_path,
            )
        elif args.mode == "mtls_roles":
            generator.generate_mtls_roles_config(
                host=args.host,
                port=args.port,
                cert_file=args.cert_file,
                key_file=args.key_file,
                ca_cert_file=args.ca_cert_file,
                output_path=output_path,
            )

        print(f"✅ Generated {args.mode} configuration: {output_path}")


if __name__ == "__main__":
    main()
