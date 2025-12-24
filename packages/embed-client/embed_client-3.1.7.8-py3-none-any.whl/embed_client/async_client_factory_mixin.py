"""
Factory helpers (from_config*, with_auth) for EmbeddingServiceAsyncClient.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union

from embed_client.config import ClientConfig


class AsyncClientFactoryMixin:
    """Mixin that provides factory classmethods for the async client."""

    @classmethod
    def from_config(
        cls,
        config: ClientConfig,
    ) -> Any:
        """Create client from an existing ClientConfig object."""
        return cls(config=config)  # type: ignore[call-arg]

    @classmethod
    def from_config_dict(
        cls,
        config_dict: Dict[str, Any],
    ) -> Any:
        """Create client from a configuration dictionary."""
        return cls(config_dict=config_dict)  # type: ignore[call-arg]

    @classmethod
    def from_config_file(
        cls,
        config_path: Union[str, Path],
    ) -> Any:
        """Create client from configuration file path."""
        client_config = ClientConfig(str(config_path))
        client_config.load_config()
        return cls(config=client_config)  # type: ignore[call-arg]

    @classmethod
    def with_auth(
        cls,
        base_url: str,
        port: int,
        auth_method: str,
        **kwargs: Any,
    ) -> Any:
        """
        Create client with authentication configuration.

        Supports ``api_key``, ``jwt``, ``basic``, ``certificate`` methods.
        """
        config_dict: Dict[str, Any] = {
            "server": {"host": base_url, "port": port},
            "client": {"timeout": kwargs.get("timeout", 30.0)},
            "auth": {"method": auth_method},
        }

        if auth_method == "api_key":
            if "api_keys" in kwargs:
                config_dict["auth"]["api_keys"] = kwargs["api_keys"]
            elif "api_key" in kwargs:
                config_dict["auth"]["api_keys"] = {"user": kwargs["api_key"]}
            else:
                raise ValueError(
                    "api_keys or api_key parameter required for api_key authentication"
                )
        elif auth_method == "jwt":
            required_params = ["secret", "username", "password"]
            for param in required_params:
                if param not in kwargs:
                    raise ValueError(
                        f"{param} parameter required for jwt authentication"
                    )
            config_dict["auth"]["jwt"] = {
                "secret": kwargs["secret"],
                "username": kwargs["username"],
                "password": kwargs["password"],
                "expiry_hours": kwargs.get("expiry_hours", 24),
            }
        elif auth_method == "basic":
            required_params = ["username", "password"]
            for param in required_params:
                if param not in kwargs:
                    raise ValueError(
                        f"{param} parameter required for basic authentication"
                    )
            config_dict["auth"]["basic"] = {
                "username": kwargs["username"],
                "password": kwargs["password"],
            }
        elif auth_method == "certificate":
            required_params = ["cert_file", "key_file"]
            for param in required_params:
                if param not in kwargs:
                    raise ValueError(
                        f"{param} parameter required for certificate authentication"
                    )
            config_dict["auth"]["certificate"] = {
                "cert_file": kwargs["cert_file"],
                "key_file": kwargs["key_file"],
            }
        else:
            raise ValueError(f"Unsupported authentication method: {auth_method}")

        ssl_enabled = kwargs.get("ssl_enabled")
        if ssl_enabled is None:
            ssl_enabled = base_url.startswith("https://")

        if ssl_enabled or any(
            key in kwargs
            for key in ["ca_cert_file", "cert_file", "key_file", "ssl_enabled"]
        ):
            ssl_config: Dict[str, Any] = {
                "enabled": ssl_enabled,
                "verify_mode": kwargs.get("verify_mode", "CERT_REQUIRED"),
                "check_hostname": kwargs.get("check_hostname", True),
                "check_expiry": kwargs.get("check_expiry", True),
            }
            if "ca_cert_file" in kwargs:
                ssl_config["ca_cert_file"] = kwargs["ca_cert_file"]
            if "cert_file" in kwargs:
                ssl_config["cert_file"] = kwargs["cert_file"]
            if "key_file" in kwargs:
                ssl_config["key_file"] = kwargs["key_file"]
            config_dict["ssl"] = ssl_config

        return cls(config_dict=config_dict)  # type: ignore[call-arg]


__all__ = ["AsyncClientFactoryMixin"]
