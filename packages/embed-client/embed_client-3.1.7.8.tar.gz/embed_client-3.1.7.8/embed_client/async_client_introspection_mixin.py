"""
Introspection and diagnostics helpers for EmbeddingServiceAsyncClient.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import os
from typing import Any, Dict, List


class AsyncClientIntrospectionMixin:
    """Mixin that exposes auth and SSL diagnostic helpers."""

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests (adapter handles real auth)."""
        return {}

    def is_authenticated(self) -> bool:
        """Return True when client is configured to use any auth method."""
        if getattr(self, "auth_manager", None) is not None:
            return self.auth_manager.is_auth_enabled()  # type: ignore[attr-defined]

        if getattr(self, "config_dict", None) is not None:
            return self.config_dict.get("auth", {}).get("method", "none") != "none"  # type: ignore[attr-defined]

        if getattr(self, "config", None) is not None:
            return self.config.get("auth.method", "none") != "none"  # type: ignore[attr-defined]

        return False

    def get_auth_method(self) -> str:
        """Return current authentication method name or \"none\"."""
        if getattr(self, "auth_manager", None) is not None:
            return self.auth_manager.get_auth_method()  # type: ignore[attr-defined]

        if getattr(self, "config_dict", None) is not None:
            return self.config_dict.get("auth", {}).get("method", "none")  # type: ignore[attr-defined]

        if getattr(self, "config", None) is not None:
            return self.config.get("auth.method", "none")  # type: ignore[attr-defined]

        return "none"

    def is_ssl_enabled(self) -> bool:
        """Return True when SSL/TLS is enabled in config."""
        if getattr(self, "config_dict", None) is not None:
            return self.config_dict.get("ssl", {}).get("enabled", False)  # type: ignore[attr-defined]

        if getattr(self, "config", None) is not None:
            return self.config.get("ssl.enabled", False)  # type: ignore[attr-defined]

        return False

    def is_mtls_enabled(self) -> bool:
        """Return True when mTLS is enabled (cert+key configured)."""
        if getattr(self, "config_dict", None) is not None:
            ssl_config = self.config_dict.get("ssl", {})  # type: ignore[attr-defined]
            return bool(
                ssl_config.get("enabled", False)
                and ssl_config.get("cert_file")
                and ssl_config.get("key_file")
            )

        if getattr(self, "config", None) is not None:
            ssl_config = self.config.get("ssl", {})  # type: ignore[attr-defined]
            return bool(
                ssl_config.get("enabled", False)
                and ssl_config.get("cert_file")
                and ssl_config.get("key_file")
            )

        return False

    def get_ssl_config(self) -> Dict[str, Any]:
        """Return current SSL configuration dictionary."""
        if getattr(self, "config_dict", None) is not None:
            return self.config_dict.get("ssl", {})  # type: ignore[attr-defined]

        if getattr(self, "config", None) is not None:
            return self.config.get("ssl", {})  # type: ignore[attr-defined]

        return {}

    def validate_ssl_config(self) -> List[str]:
        """Validate SSL configuration files (paths only; adapter handles SSL itself)."""
        errors: List[str] = []
        ssl_config: Dict[str, Any]

        if getattr(self, "config_dict", None) is not None:
            ssl_config = self.config_dict.get("ssl", {})  # type: ignore[attr-defined]
        elif getattr(self, "config", None) is not None:
            ssl_config = self.config.get("ssl", {})  # type: ignore[attr-defined]
        else:
            return errors

        if ssl_config.get("enabled", False):
            cert_file = ssl_config.get("cert_file")
            key_file = ssl_config.get("key_file")
            ca_cert_file = ssl_config.get("ca_cert_file")

            if cert_file and not os.path.exists(cert_file):
                errors.append(f"Certificate file not found: {cert_file}")
            if key_file and not os.path.exists(key_file):
                errors.append(f"Key file not found: {key_file}")
            if ca_cert_file and not os.path.exists(ca_cert_file):
                errors.append(f"CA certificate file not found: {ca_cert_file}")

        return errors

    def get_supported_ssl_protocols(self) -> List[str]:
        """Return list of supported SSL/TLS protocol names (for diagnostics only)."""
        return ["TLSv1.2", "TLSv1.3"]


__all__ = ["AsyncClientIntrospectionMixin"]
