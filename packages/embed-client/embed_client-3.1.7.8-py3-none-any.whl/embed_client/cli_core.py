"""
Core implementation of the embed-client CLI.

Provides the `VectorizationCLI` class and configuration helpers used by the
user-facing `embed_client.cli` entry point.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.client_factory import ClientFactory
from embed_client.config import ClientConfig
from embed_client.response_parsers import extract_embeddings


class VectorizationCLI:
    """CLI application for text vectorization using embed-client library.

    This class encapsulates the core logic of the `embed-vectorize` command,
    including connection management, health checks, embedding requests, and
    queue operations. It relies exclusively on the `EmbeddingServiceAsyncClient`
    and related helpers from the embed-client package.
    """

    def __init__(self) -> None:
        """Initialize a new VectorizationCLI instance."""
        self.client: Optional[EmbeddingServiceAsyncClient] = None

    async def connect(
        self,
        config: Optional[ClientConfig] = None,
        config_dict: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Connect to the embedding service using provided configuration.

        The client is created via `ClientFactory` or directly from a
        `ClientConfig` / configuration dictionary. All low-level transport and
        authentication details are handled by the embed-client library.

        Args:
            config: Optional `ClientConfig` instance.
            config_dict: Optional raw configuration dictionary.

        Returns:
            True if connection was established successfully, False otherwise.
        """
        try:
            if config is not None:
                self.client = EmbeddingServiceAsyncClient.from_config(config)
            elif config_dict is not None:
                self.client = EmbeddingServiceAsyncClient(config_dict=config_dict)
            else:
                # Use ClientFactory.from_environment() as fallback
                self.client = ClientFactory.from_environment()

            await self.client.__aenter__()
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Failed to connect: {exc}", file=sys.stderr)
            return False

    async def disconnect(self) -> None:
        """Close the underlying client connection if it exists."""
        if self.client is not None:
            await self.client.close()

    async def health_check(self) -> bool:
        """Perform a health check against the embedding service."""
        try:
            assert self.client is not None
            result = await self.client.health()
            print(json.dumps(result, indent=2))
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Health check failed: {exc}", file=sys.stderr)
            return False

    async def vectorize_texts(
        self,
        texts: List[str],
        output_format: str = "json",
        show_full_data: bool = False,
    ) -> Optional[List[List[float]]]:
        """Vectorize texts using the high-level `embed` helper.

        Notes:
            - Always uses ``error_policy=\"continue\"`` to align with the
              Embedding Service contract, so per-item validation errors are
              exposed via ``data[\"results\"][i][\"error\"]``.
            - All input validation is delegated to the server.

        Args:
            texts: List of input texts to embed.
            output_format: One of ``\"json\"``, ``\"csv\"``, or ``\"vectors\"``.
            show_full_data: If True, print full embedding payload instead of
                only vectors.

        Returns:
            A list of embedding vectors when `show_full_data` is False,
            otherwise ``None``.
        """
        try:
            assert self.client is not None

            # Always use error_policy="continue" for batch safety and per-item errors
            data = await self.client.embed(texts, error_policy="continue")

            if show_full_data:
                if output_format == "json":
                    print(json.dumps(data, indent=2))
                else:
                    embeddings = data.get("embeddings") or []
                    if output_format == "csv":
                        self._print_csv(embeddings)
                    elif output_format == "vectors":
                        self._print_vectors(embeddings)
                return None

            embeddings = data.get("embeddings")
            if embeddings is None:
                # Fallback to response_parsers for legacy-style responses
                wrapped: Dict[str, Any] = {"result": {"success": True, "data": data}}
                embeddings = extract_embeddings(wrapped)

            if output_format == "json":
                print(json.dumps(embeddings, indent=2))
            elif output_format == "csv":
                self._print_csv(embeddings)
            elif output_format == "vectors":
                self._print_vectors(embeddings)

            return embeddings
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Vectorization failed: {exc}", file=sys.stderr)
            return None

    def _print_csv(self, embeddings: List[List[float]]) -> None:
        """Print embeddings in CSV format."""
        for idx, embedding in enumerate(embeddings):
            print(f"text_{idx}," + ",".join(map(str, embedding)))

    def _print_vectors(self, embeddings: List[List[float]]) -> None:
        """Print embeddings as human-readable vectors."""
        for idx, embedding in enumerate(embeddings):
            print(f"Text {idx}: [{', '.join(map(str, embedding))}]")

    async def get_help(self, command: Optional[str] = None) -> None:
        """Fetch help information from the embedding service."""
        try:
            assert self.client is not None
            if command:
                result = await self.client.cmd("help", params={"command": command})
            else:
                result = await self.client.cmd("help")
            print(json.dumps(result, indent=2))
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Help request failed: {exc}", file=sys.stderr)

    async def get_commands(self) -> None:
        """List all available commands from the embedding service."""
        try:
            assert self.client is not None
            result = await self.client.get_commands()
            print(json.dumps(result, indent=2))
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Commands request failed: {exc}", file=sys.stderr)

    async def queue_list(
        self, status: Optional[str] = None, limit: Optional[int] = None
    ) -> None:
        """List queued commands."""
        try:
            assert self.client is not None
            result = await self.client.list_queued_commands(status=status, limit=limit)
            print(json.dumps(result, indent=2))
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Failed to list queue: {exc}", file=sys.stderr)

    async def queue_status(self, job_id: str) -> None:
        """Get the status of a specific job."""
        try:
            assert self.client is not None
            result = await self.client.job_status(job_id)
            print(json.dumps(result, indent=2))
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Failed to get job status: {exc}", file=sys.stderr)

    async def queue_cancel(self, job_id: str) -> None:
        """Cancel a queued or running job."""
        try:
            assert self.client is not None
            result = await self.client.cancel_command(job_id)
            print(json.dumps(result, indent=2))
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Failed to cancel job: {exc}", file=sys.stderr)

    async def queue_wait(
        self, job_id: str, timeout: float = 60.0, poll_interval: float = 1.0
    ) -> None:
        """Wait for completion of a specific job."""
        try:
            assert self.client is not None
            result = await self.client.wait_for_job(
                job_id, timeout=timeout, poll_interval=poll_interval
            )
            print(json.dumps(result, indent=2))
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Failed to wait for job: {exc}", file=sys.stderr)

    async def queue_logs(self, job_id: str) -> None:
        """Fetch logs for a specific job."""
        try:
            assert self.client is not None
            result = await self.client.get_job_logs(job_id)
            print(json.dumps(result, indent=2))
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Failed to get job logs: {exc}", file=sys.stderr)


def create_config_from_args(args: Any) -> Dict[str, Any]:
    """Create a configuration dictionary from parsed CLI arguments.

    This helper mirrors the shape of the JSON configuration files used by
    `ClientConfig` and `ClientFactory`, allowing the CLI to construct a
    `ClientConfig` instance without requiring callers to manage JSON files.
    """
    config: Dict[str, Any] = {
        "server": {"host": args.host, "port": args.port},
        "auth": {"method": "none"},
        "ssl": {"enabled": False},
        "client": {"timeout": getattr(args, "timeout", 30.0)},
    }

    # Add authentication if specified
    if getattr(args, "api_key", None):
        config["auth"]["method"] = "api_key"
        config["auth"]["api_keys"] = {"user": args.api_key}
        if getattr(args, "api_key_header", None):
            config["auth"]["api_key_header"] = args.api_key_header
    elif getattr(args, "jwt_secret", None):
        config["auth"]["method"] = "jwt"
        config["auth"]["jwt"] = {
            "secret": args.jwt_secret,
            "username": getattr(args, "jwt_username", ""),
            "password": getattr(args, "jwt_password", ""),
        }
    elif getattr(args, "basic_username", None):
        config["auth"]["method"] = "basic"
        config["auth"]["basic"] = {
            "username": args.basic_username,
            "password": getattr(args, "basic_password", ""),
        }

    # Add SSL if specified
    if (
        getattr(args, "ssl", False)
        or getattr(args, "cert_file", None)
        or getattr(args, "key_file", None)
    ):
        config["ssl"]["enabled"] = True
        if getattr(args, "cert_file", None):
            config["ssl"]["cert_file"] = args.cert_file
        if getattr(args, "key_file", None):
            config["ssl"]["key_file"] = args.key_file
        if getattr(args, "ca_cert_file", None):
            config["ssl"]["ca_cert_file"] = args.ca_cert_file

    return config
