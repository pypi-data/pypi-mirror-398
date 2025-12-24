"""
Core components for Security CLI (client + config helpers).

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.response_parsers import extract_embeddings


class SecurityCLI:
    """CLI application supporting all 8 security modes."""

    def __init__(self) -> None:
        self.client: Optional[EmbeddingServiceAsyncClient] = None

    async def connect(self, config: Dict[str, Any]) -> bool:
        """Connect to embedding service using provided configuration."""
        try:
            self.client = EmbeddingServiceAsyncClient(config_dict=config)
            await self.client.__aenter__()
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Failed to connect: {exc}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from embedding service."""
        if self.client:
            await self.client.__aexit__(None, None, None)

    async def health_check(self) -> bool:
        """Check service health."""
        if not self.client:
            print("❌ Client is not connected")
            return False
        try:
            result = await self.client.health()
            print(f"✅ Service health: {result.get('status', 'unknown')}")
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Health check failed: {exc}")
            return False

    async def vectorize_texts(
        self,
        texts: List[str],
        output_format: str = "json",
    ) -> Optional[List[List[float]]]:
        """Vectorize texts and print them in the requested format."""
        if not self.client:
            print("❌ Client is not connected")
            return None
        try:
            params: Dict[str, Any] = {"texts": texts}
            result = await self.client.cmd("embed", params=params)

            embeddings = extract_embeddings(result)

            if output_format == "json":
                print(json.dumps(embeddings, indent=2))
            elif output_format == "csv":
                self._print_csv(embeddings)
            elif output_format == "vectors":
                self._print_vectors(embeddings)

            return embeddings
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Vectorization failed: {exc}")
            return None

    async def get_help(self, command: Optional[str] = None) -> None:
        """Get help information from the service."""
        if not self.client:
            print("❌ Client is not connected")
            return
        try:
            if command:
                result = await self.client.cmd("help", params={"command": command})
            else:
                result = await self.client.cmd("help")
            print(json.dumps(result, indent=2))
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Help request failed: {exc}")

    async def get_commands(self) -> None:
        """Get available commands from the service."""
        if not self.client:
            print("❌ Client is not connected")
            return
        try:
            result = await self.client.get_commands()
            print(json.dumps(result, indent=2))
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Commands request failed: {exc}")

    def _print_csv(self, embeddings: List[List[float]]) -> None:
        """Print embeddings in CSV format."""
        for index, embedding in enumerate(embeddings):
            print(f"text_{index}," + ",".join(map(str, embedding)))

    def _print_vectors(self, embeddings: List[List[float]]) -> None:
        """Print embeddings as vectors."""
        for index, embedding in enumerate(embeddings):
            print(f"Text {index}: [{', '.join(map(str, embedding))}]")


def create_config_from_security_mode(
    security_mode: str,
    host: str,
    port: int,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Create configuration dictionary based on security mode."""

    config: Dict[str, Any] = {
        "server": {"host": host, "port": port},
        "auth": {"method": "none"},
        "ssl": {"enabled": False},
        "security": {"enabled": False},
    }

    if security_mode == "http":
        config["server"]["host"] = f"http://{host.split('://')[-1]}"

    elif security_mode == "http_token":
        config["server"]["host"] = f"http://{host.split('://')[-1]}"
        config["auth"]["method"] = "api_key"
        config["security"] = {
            "enabled": True,
            "tokens": {"user": kwargs.get("api_key", "admin-secret-key")},
        }

    elif security_mode == "http_token_roles":
        config["server"]["host"] = f"http://{host.split('://')[-1]}"
        config["auth"]["method"] = "api_key"
        config["security"] = {
            "enabled": True,
            "tokens": {"user": kwargs.get("api_key", "admin-secret-key")},
            "roles": {
                "admin": ["read", "write", "delete", "admin"],
                "user": ["read", "write"],
                "readonly": ["read"],
            },
        }

    elif security_mode == "https":
        config["server"]["host"] = f"https://{host.split('://')[-1]}"
        config["ssl"] = {
            "enabled": True,
            "verify": False,
            "cert_file": kwargs.get("cert_file"),
            "key_file": kwargs.get("key_file"),
            "ca_cert_file": kwargs.get("ca_cert_file"),
        }

    elif security_mode == "https_token":
        config["server"]["host"] = f"https://{host.split('://')[-1]}"
        config["auth"]["method"] = "api_key"
        config["ssl"] = {
            "enabled": True,
            "cert_file": kwargs.get("cert_file"),
            "key_file": kwargs.get("key_file"),
        }
        config["security"] = {
            "enabled": True,
            "tokens": {"user": kwargs.get("api_key", "admin-secret-key")},
        }

    elif security_mode == "https_token_roles":
        config["server"]["host"] = f"https://{host.split('://')[-1]}"
        config["auth"]["method"] = "api_key"
        config["ssl"] = {
            "enabled": True,
            "cert_file": kwargs.get("cert_file"),
            "key_file": kwargs.get("key_file"),
        }
        config["security"] = {
            "enabled": True,
            "tokens": {"user": kwargs.get("api_key", "admin-secret-key")},
            "roles": {
                "admin": ["read", "write", "delete", "admin"],
                "user": ["read", "write"],
                "readonly": ["read"],
            },
        }

    elif security_mode == "mtls":
        config["server"]["host"] = f"https://{host.split('://')[-1]}"
        config["auth"]["method"] = "certificate"
        config["ssl"] = {
            "enabled": True,
            "cert_file": kwargs.get("cert_file"),
            "key_file": kwargs.get("key_file"),
            "ca_cert_file": kwargs.get("ca_cert_file"),
        }

    elif security_mode == "mtls_roles":
        config["server"]["host"] = f"https://{host.split('://')[-1]}"
        config["auth"]["method"] = "certificate"
        config["ssl"] = {
            "enabled": True,
            "cert_file": kwargs.get("cert_file"),
            "key_file": kwargs.get("key_file"),
            "ca_cert_file": kwargs.get("ca_cert_file"),
        }
        config["security"] = {
            "enabled": True,
            "roles": {
                "admin": ["read", "write", "delete", "admin"],
                "user": ["read", "write"],
                "readonly": ["read"],
            },
        }

    return config


__all__ = ["SecurityCLI", "create_config_from_security_mode"]
