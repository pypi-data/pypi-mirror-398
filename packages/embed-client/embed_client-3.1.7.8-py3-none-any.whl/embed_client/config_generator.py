"""
Configuration Generator for embed-client.

Generates client configurations for all security modes:
- http
- http + token
- http + token + roles
- https
- https + token
- https + token + roles
- mtls
- mtls + roles

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ClientConfigGenerator:
    """Generator for embed-client configurations."""

    def __init__(self):
        """Initialize configuration generator."""
        self.default_tokens = {
            "admin": "admin-secret-key",
            "user": "user-secret-key",
            "readonly": "readonly-secret-key",
        }
        self.default_roles = {
            "admin": ["read", "write", "delete", "admin"],
            "user": ["read", "write"],
            "readonly": ["read"],
        }

    def generate_http_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate HTTP configuration without authentication."""
        config: Dict[str, Any] = {
            "server": {"host": host, "port": port},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
            "security": {"enabled": False},
        }
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_http_token_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        api_key: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate HTTP configuration with token authentication."""
        token = api_key or self.default_tokens["user"]
        config: Dict[str, Any] = {
            "server": {"host": host, "port": port},
            "auth": {"method": "api_key", "api_keys": {"user": token}},
            "ssl": {"enabled": False},
            "security": {"enabled": True, "tokens": {"user": token}},
        }
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_http_token_roles_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        api_key: Optional[str] = None,
        tokens: Optional[Dict[str, str]] = None,
        roles: Optional[Dict[str, List[str]]] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate HTTP configuration with token authentication and roles."""
        tokens_dict = tokens or self.default_tokens
        roles_dict = roles or self.default_roles
        token = api_key or tokens_dict.get("admin", "admin-secret-key")
        config: Dict[str, Any] = {
            "server": {"host": host, "port": port},
            "auth": {"method": "api_key", "api_keys": {"admin": token}},
            "ssl": {"enabled": False},
            "security": {
                "enabled": True,
                "tokens": tokens_dict,
                "roles": roles_dict,
            },
        }
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_https_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate HTTPS configuration without authentication."""
        config: Dict[str, Any] = {
            "server": {"host": host, "port": port},
            "auth": {"method": "none"},
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
            },
            "security": {"enabled": False},
        }
        if cert_file:
            config["ssl"]["cert_file"] = cert_file
        if key_file:
            config["ssl"]["key_file"] = key_file
        if ca_cert_file:
            config["ssl"]["ca_cert_file"] = ca_cert_file
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_https_token_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        api_key: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate HTTPS configuration with token authentication."""
        token = api_key or self.default_tokens["user"]
        config: Dict[str, Any] = {
            "server": {"host": host, "port": port},
            "auth": {"method": "api_key", "api_keys": {"user": token}},
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
            },
            "security": {"enabled": True, "tokens": {"user": token}},
        }
        if cert_file:
            config["ssl"]["cert_file"] = cert_file
        if key_file:
            config["ssl"]["key_file"] = key_file
        if ca_cert_file:
            config["ssl"]["ca_cert_file"] = ca_cert_file
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_https_token_roles_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        api_key: Optional[str] = None,
        tokens: Optional[Dict[str, str]] = None,
        roles: Optional[Dict[str, List[str]]] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate HTTPS configuration with token authentication and roles."""
        tokens_dict = tokens or self.default_tokens
        roles_dict = roles or self.default_roles
        token = api_key or tokens_dict.get("admin", "admin-secret-key")
        config: Dict[str, Any] = {
            "server": {"host": host, "port": port},
            "auth": {"method": "api_key", "api_keys": {"admin": token}},
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
            },
            "security": {
                "enabled": True,
                "tokens": tokens_dict,
                "roles": roles_dict,
            },
        }
        if cert_file:
            config["ssl"]["cert_file"] = cert_file
        if key_file:
            config["ssl"]["key_file"] = key_file
        if ca_cert_file:
            config["ssl"]["ca_cert_file"] = ca_cert_file
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_mtls_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate mTLS configuration with client certificates."""
        config: Dict[str, Any] = {
            "server": {"host": host, "port": port},
            "auth": {"method": "certificate"},
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_REQUIRED",
                "check_hostname": False,
            },
            "security": {"enabled": False},
        }
        if cert_file:
            config["ssl"]["cert_file"] = cert_file
            config["auth"]["certificate"] = {"cert_file": cert_file}
        if key_file:
            config["ssl"]["key_file"] = key_file
            if "certificate" not in config["auth"]:
                config["auth"]["certificate"] = {}
            config["auth"]["certificate"]["key_file"] = key_file
        if ca_cert_file:
            config["ssl"]["ca_cert_file"] = ca_cert_file
            if "certificate" not in config["auth"]:
                config["auth"]["certificate"] = {}
            config["auth"]["certificate"]["ca_cert_file"] = ca_cert_file
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_mtls_roles_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        roles: Optional[Dict[str, List[str]]] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Generate mTLS configuration with client certificates and roles."""
        roles_dict = roles or self.default_roles
        config: Dict[str, Any] = {
            "server": {"host": host, "port": port},
            "auth": {"method": "certificate"},
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_REQUIRED",
                "check_hostname": False,
            },
            "security": {"enabled": True, "roles": roles_dict},
        }
        if cert_file:
            config["ssl"]["cert_file"] = cert_file
            config["auth"]["certificate"] = {"cert_file": cert_file}
        if key_file:
            config["ssl"]["key_file"] = key_file
            if "certificate" not in config["auth"]:
                config["auth"]["certificate"] = {}
            config["auth"]["certificate"]["key_file"] = key_file
        if ca_cert_file:
            config["ssl"]["ca_cert_file"] = ca_cert_file
            if "certificate" not in config["auth"]:
                config["auth"]["certificate"] = {}
            config["auth"]["certificate"]["ca_cert_file"] = ca_cert_file
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_all_configs(
        self,
        host: str = "localhost",
        port: int = 8001,
        output_dir: Optional[Path] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Generate all 8 security mode configurations."""
        configs = {}

        # 1. HTTP
        configs["http"] = self.generate_http_config(
            host=host,
            port=port,
            output_path=output_dir / "http.json" if output_dir else None,
        )

        # 2. HTTP + Token
        configs["http_token"] = self.generate_http_token_config(
            host=host,
            port=port,
            output_path=output_dir / "http_token.json" if output_dir else None,
        )

        # 3. HTTP + Token + Roles
        configs["http_token_roles"] = self.generate_http_token_roles_config(
            host=host,
            port=port,
            output_path=output_dir / "http_token_roles.json" if output_dir else None,
        )

        # 4. HTTPS
        configs["https"] = self.generate_https_config(
            host=host,
            port=port,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            output_path=output_dir / "https.json" if output_dir else None,
        )

        # 5. HTTPS + Token
        configs["https_token"] = self.generate_https_token_config(
            host=host,
            port=port,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            output_path=output_dir / "https_token.json" if output_dir else None,
        )

        # 6. HTTPS + Token + Roles
        configs["https_token_roles"] = self.generate_https_token_roles_config(
            host=host,
            port=port,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            output_path=output_dir / "https_token_roles.json" if output_dir else None,
        )

        # 7. mTLS
        configs["mtls"] = self.generate_mtls_config(
            host=host,
            port=port,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            output_path=output_dir / "mtls.json" if output_dir else None,
        )

        # 8. mTLS + Roles
        configs["mtls_roles"] = self.generate_mtls_roles_config(
            host=host,
            port=port,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            output_path=output_dir / "mtls_roles.json" if output_dir else None,
        )

        return configs

    def _save_config(self, config: Dict[str, Any], output_path: Path) -> None:
        """Save configuration to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"Configuration saved to {output_path}")
