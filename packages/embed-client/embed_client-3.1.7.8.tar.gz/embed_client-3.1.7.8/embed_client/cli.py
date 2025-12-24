#!/usr/bin/env python3
"""
CLI Application for Text Vectorization
Command-line interface for embedding text using embed-client.

This CLI is fully based on the embed-client library and uses:
- ClientFactory for client creation
- ClientConfig for configuration management
- response_parsers for data extraction
- All authentication methods (API Key, JWT, Basic, Certificate)
- Queue management commands

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import argparse
import asyncio
import sys
from typing import Any, Dict  # noqa: F401

from embed_client.config import ClientConfig
from embed_client.cli_core import VectorizationCLI, create_config_from_args


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="CLI Application for Text Vectorization (fully based on embed-client library)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Vectorize text from command line
  python -m embed_client vectorize "hello world" "test text"

  # Vectorize text from file
  python -m embed_client vectorize --file texts.txt

  # Use HTTPS with API key authentication
  python -m embed_client vectorize "hello world" --host https://localhost --port 8443 --api-key your-key

  # Use mTLS with client certificates
  python -m embed_client vectorize "hello world" --ssl --cert-file client.crt --key-file client.key

  # Use JWT authentication
  python -m embed_client vectorize "hello" --jwt-secret secret --jwt-username user --jwt-password pass

  # Use config file
  python -m embed_client --config config.json vectorize "hello"

  # Queue management
  python -m embed_client queue-list
  python -m embed_client queue-status JOB_ID
  python -m embed_client queue-cancel JOB_ID
  python -m embed_client queue-wait JOB_ID

  # Get help from service
  python -m embed_client help

  # Check service health
  python -m embed_client health
        """,
    )

    # Global options
    parser.add_argument(
        "--config", "-c", help="Path to configuration file (JSON or YAML)"
    )
    parser.add_argument(
        "--host",
        default="http://localhost",
        help="Server host (default: http://localhost)",
    )
    parser.add_argument(
        "--port", type=int, default=8001, help="Server port (default: 8001)"
    )
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="Request timeout in seconds"
    )

    # Authentication options
    auth_group = parser.add_argument_group("authentication")
    auth_group.add_argument("--api-key", help="API key for authentication")
    auth_group.add_argument(
        "--api-key-header", help="API key header name (default: X-API-Key)"
    )
    auth_group.add_argument("--jwt-secret", help="JWT secret for authentication")
    auth_group.add_argument("--jwt-username", help="JWT username")
    auth_group.add_argument("--jwt-password", help="JWT password")
    auth_group.add_argument("--basic-username", help="Basic auth username")
    auth_group.add_argument("--basic-password", help="Basic auth password")

    # SSL/TLS options
    ssl_group = parser.add_argument_group("ssl/tls")
    ssl_group.add_argument("--ssl", action="store_true", help="Enable SSL/TLS")
    ssl_group.add_argument("--cert-file", help="Client certificate file")
    ssl_group.add_argument("--key-file", help="Client private key file")
    ssl_group.add_argument("--ca-cert-file", help="CA certificate file")

    # Commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Vectorize command
    vectorize_parser = subparsers.add_parser("vectorize", help="Vectorize text")
    vectorize_parser.add_argument("texts", nargs="*", help="Texts to vectorize")
    vectorize_parser.add_argument(
        "--file", "-f", help="File containing texts (one per line)"
    )
    vectorize_parser.add_argument(
        "--format",
        choices=["json", "csv", "vectors"],
        default="json",
        help="Output format (default: json)",
    )
    vectorize_parser.add_argument(
        "--full-data",
        action="store_true",
        help="Show full embedding data (body, embedding, tokens, bm25_tokens)",
    )

    # Health command
    subparsers.add_parser("health", help="Check service health")

    # Help command
    help_parser = subparsers.add_parser("help", help="Get help from service")
    help_parser.add_argument("--command", help="Specific command to get help for")

    # Commands command
    subparsers.add_parser("commands", help="Get available commands")

    # Queue commands
    queue_list_parser = subparsers.add_parser("queue-list", help="List queued commands")
    queue_list_parser.add_argument("--status", help="Filter by status")
    queue_list_parser.add_argument("--limit", type=int, help="Limit number of results")

    queue_status_parser = subparsers.add_parser("queue-status", help="Get job status")
    queue_status_parser.add_argument("job_id", help="Job identifier")

    queue_cancel_parser = subparsers.add_parser("queue-cancel", help="Cancel a job")
    queue_cancel_parser.add_argument("job_id", help="Job identifier")

    queue_wait_parser = subparsers.add_parser(
        "queue-wait", help="Wait for job completion"
    )
    queue_wait_parser.add_argument("job_id", help="Job identifier")
    queue_wait_parser.add_argument(
        "--timeout", type=float, default=60.0, help="Timeout in seconds"
    )
    queue_wait_parser.add_argument(
        "--poll-interval", type=float, default=1.0, help="Poll interval in seconds"
    )

    queue_logs_parser = subparsers.add_parser("queue-logs", help="Get job logs")
    queue_logs_parser.add_argument("job_id", help="Job identifier")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Load configuration
    config = None
    config_dict = None

    if args.config:
        # Load from config file using ClientConfig
        config = ClientConfig(args.config)
        config.load_config()
    else:
        # Create config from command line arguments
        config_dict = create_config_from_args(args)

    # Create CLI instance
    cli = VectorizationCLI()

    try:
        # Connect to service
        if not await cli.connect(config=config, config_dict=config_dict):
            return 1

        # Execute command
        if args.command == "vectorize":
            texts = args.texts
            if args.file:
                with open(args.file, "r") as f:
                    texts.extend(line.strip() for line in f if line.strip())

            if not texts:
                print("❌ No texts provided", file=sys.stderr)
                return 1

            await cli.vectorize_texts(texts, args.format, args.full_data)

        elif args.command == "health":
            await cli.health_check()

        elif args.command == "help":
            await cli.get_help(getattr(args, "command", None))

        elif args.command == "commands":
            await cli.get_commands()

        elif args.command == "queue-list":
            await cli.queue_list(
                getattr(args, "status", None), getattr(args, "limit", None)
            )

        elif args.command == "queue-status":
            await cli.queue_status(args.job_id)

        elif args.command == "queue-cancel":
            await cli.queue_cancel(args.job_id)

        elif args.command == "queue-wait":
            await cli.queue_wait(
                args.job_id,
                timeout=getattr(args, "timeout", 60.0),
                poll_interval=getattr(args, "poll_interval", 1.0),
            )

        elif args.command == "queue-logs":
            await cli.queue_logs(args.job_id)

        return 0

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1
    finally:
        await cli.disconnect()


def cli_main():
    """Synchronous entry point for CLI command."""
    return asyncio.run(main())


if __name__ == "__main__":
    sys.exit(cli_main())
