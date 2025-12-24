"""
Client configuration management module.

This module provides configuration management for the embed-client,
supporting all security modes and authentication methods.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import os
from copy import deepcopy
from typing import Any, Dict, List, Optional

from embed_client.config_defaults import DEFAULT_CONFIG, update_nested_dict
from embed_client.config_presets import (
    create_http_config_for_class,
    create_http_token_config_for_class,
    create_https_config_for_class,
    create_https_token_config_for_class,
    create_mtls_config_for_class,
    create_minimal_config_dict,
    create_secure_config_dict,
    load_env_variables,
    validate_client_config,
)


class ClientConfig:
    """
    Configuration management class for the embed-client.
    Allows loading settings from configuration file and environment variables.
    Supports all security modes and authentication methods.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize client configuration.

        Args:
            config_path: Path to configuration file. If not specified,
                        "./config.json" is used.
        """
        self.config_path = config_path or "./config.json"
        self.config_data: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """
        Load configuration from file and environment variables.
        """
        # Set default config values (deep copy to avoid global mutation)
        self.config_data = deepcopy(DEFAULT_CONFIG)

        # Try to load configuration from file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    update_nested_dict(self.config_data, file_config)
            except Exception as e:
                print(f"Error loading config from {self.config_path}: {e}")

        # Load configuration from environment variables
        load_env_variables(self.config_data)

    def load_from_file(self, config_path: str) -> None:
        """
        Load configuration from the specified file.

        Args:
            config_path: Path to configuration file.
        """
        self.config_path = config_path
        self.load_config()

    def load_config_file(self, config_path: str) -> None:
        """Backward-compatible alias for :meth:`load_from_file`."""
        self.load_from_file(config_path)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value for key.

        Args:
            key: Configuration key in format "section.param"
            default: Default value if key not found

        Returns:
            Configuration value
        """
        parts = key.split(".")

        # Get value from config
        value = self.config_data
        for part in parts:
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]

        return value

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dictionary with all configuration values
        """
        return self.config_data.copy()

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value for key.

        Args:
            key: Configuration key in format "section.param"
            value: Configuration value
        """
        parts = key.split(".")
        if len(parts) == 1:
            self.config_data[key] = value
        else:
            section = parts[0]

            if section not in self.config_data:
                self.config_data[section] = {}

            current = self.config_data[section]
            for part in parts[1:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value

    def save(self, path: Optional[str] = None) -> None:
        """
        Save configuration to file.

        Args:
            path: Path to configuration file. If not specified,
                  self.config_path is used.
        """
        save_path = path or self.config_path
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.config_data, f, indent=2)

    def configure_auth_mode(self, mode: str, **kwargs) -> None:
        """
        Configure authentication mode.

        Args:
            mode: Authentication mode (none, api_key, jwt, certificate, basic)
            **kwargs: Additional configuration parameters
        """
        self.set("auth.method", mode)

        if mode == "api_key":
            if "key" in kwargs:
                self.set("auth.api_key.key", kwargs["key"])
            if "header" in kwargs:
                self.set("auth.api_key.header", kwargs["header"])
        elif mode == "jwt":
            if "username" in kwargs:
                self.set("auth.jwt.username", kwargs["username"])
            if "password" in kwargs:
                self.set("auth.jwt.password", kwargs["password"])
            if "secret" in kwargs:
                self.set("auth.jwt.secret", kwargs["secret"])
            if "expiry_hours" in kwargs:
                self.set("auth.jwt.expiry_hours", kwargs["expiry_hours"])
        elif mode == "certificate":
            self.set("auth.certificate.enabled", True)
            if "cert_file" in kwargs:
                self.set("auth.certificate.cert_file", kwargs["cert_file"])
            if "key_file" in kwargs:
                self.set("auth.certificate.key_file", kwargs["key_file"])
            if "ca_cert_file" in kwargs:
                self.set("auth.certificate.ca_cert_file", kwargs["ca_cert_file"])
        elif mode == "basic":
            if "username" in kwargs:
                self.set("auth.basic.username", kwargs["username"])
            if "password" in kwargs:
                self.set("auth.basic.password", kwargs["password"])

    def configure_ssl(self, enabled: bool = True, **kwargs) -> None:
        """
        Configure SSL/TLS settings.

        Args:
            enabled: Enable SSL/TLS
            **kwargs: Additional SSL configuration parameters
        """
        self.set("ssl.enabled", enabled)

        if "verify" in kwargs:
            self.set("ssl.verify", kwargs["verify"])
        if "check_hostname" in kwargs:
            self.set("ssl.check_hostname", kwargs["check_hostname"])
        if "cert_file" in kwargs:
            self.set("ssl.cert_file", kwargs["cert_file"])
        if "key_file" in kwargs:
            self.set("ssl.key_file", kwargs["key_file"])
        if "ca_cert_file" in kwargs:
            self.set("ssl.ca_cert_file", kwargs["ca_cert_file"])
        if "client_cert_required" in kwargs:
            self.set("ssl.client_cert_required", kwargs["client_cert_required"])

    def configure_server(
        self, host: str, port: int, base_url: Optional[str] = None
    ) -> None:
        """
        Configure server connection settings.

        Args:
            host: Server host
            port: Server port
            base_url: Full server URL (optional, will be constructed if not provided)
        """
        self.set("server.host", host)
        self.set("server.port", port)

        if base_url:
            self.set("server.base_url", base_url)
        else:
            protocol = "https" if self.get("ssl.enabled", False) else "http"
            self.set("server.base_url", f"{protocol}://{host}:{port}")

    def get_server_url(self) -> str:
        """
        Get the complete server URL.

        Returns:
            Server URL string
        """
        return self.get("server.base_url", "http://localhost:8001")

    def get_auth_method(self) -> str:
        """
        Get the authentication method.

        Returns:
            Authentication method string
        """
        return self.get("auth.method", "none")

    def is_ssl_enabled(self) -> bool:
        """
        Check if SSL/TLS is enabled.

        Returns:
            True if SSL is enabled, False otherwise
        """
        return self.get("ssl.enabled", False)

    def is_auth_enabled(self) -> bool:
        """
        Check if authentication is enabled.

        Returns:
            True if authentication is enabled, False otherwise
        """
        return self.get("auth.method", "none") != "none"

    def is_security_enabled(self) -> bool:
        """
        Check if security features are enabled.

        Returns:
            True if security is enabled, False otherwise
        """
        return self.get("security.enabled", False)

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of validation error messages."""
        return validate_client_config(self)

    def create_minimal_config(self) -> Dict[str, Any]:
        """Create minimal configuration with only essential features."""
        return create_minimal_config_dict(self)

    def create_secure_config(self) -> Dict[str, Any]:
        """Create secure configuration with all security features enabled."""
        return create_secure_config_dict(self)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ClientConfig":
        """
        Create ClientConfig instance from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            ClientConfig instance
        """
        config = cls()
        config.config_data = update_nested_dict(config.config_data, config_dict)
        return config

    @classmethod
    def from_file(cls, config_path: str) -> "ClientConfig":
        """
        Create ClientConfig instance from file.

        Args:
            config_path: Path to configuration file

        Returns:
            ClientConfig instance
        """
        config = cls(config_path)
        return config

    @classmethod
    def create_http_config(
        cls, host: str = "localhost", port: int = 8001
    ) -> "ClientConfig":
        """Create configuration for HTTP connection without authentication."""
        return create_http_config_for_class(cls, host=host, port=port)

    @classmethod
    def create_http_token_config(
        cls,
        host: str = "localhost",
        port: int = 8001,
        api_key: Optional[str] = None,
    ) -> "ClientConfig":
        """Create configuration for HTTP connection with API key authentication."""
        return create_http_token_config_for_class(
            cls,
            host=host,
            port=port,
            api_key=api_key,
        )

    @classmethod
    def create_https_config(
        cls,
        host: str = "localhost",
        port: int = 8443,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
    ) -> "ClientConfig":
        """Create configuration for HTTPS connection without authentication."""
        return create_https_config_for_class(
            cls,
            host=host,
            port=port,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
        )

    @classmethod
    def create_https_token_config(
        cls,
        host: str = "localhost",
        port: int = 8443,
        api_key: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
    ) -> "ClientConfig":
        """Create configuration for HTTPS connection with API key authentication."""
        return create_https_token_config_for_class(
            cls,
            host=host,
            port=port,
            api_key=api_key,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
        )

    @classmethod
    def create_mtls_config(
        cls,
        host: str = "localhost",
        port: int = 8443,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
    ) -> "ClientConfig":
        """Create configuration for mTLS connection with client certificates."""
        return create_mtls_config_for_class(
            cls,
            host=host,
            port=port,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
        )


# Singleton instance
