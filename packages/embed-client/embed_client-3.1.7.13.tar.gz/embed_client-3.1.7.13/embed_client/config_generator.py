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

    def _create_base_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        protocol: str = "http",
        token: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        crl_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create base configuration with all fields.

        Args:
            host: Server host (default value)
            port: Server port (default value)
            protocol: Protocol type (http, https, mtls)
            token: Optional authentication token
            cert_file: Optional client certificate file
            key_file: Optional client key file
            ca_cert_file: Optional CA certificate file
            crl_file: Optional CRL file

        Returns:
            Base configuration dictionary with all fields
        """
        # Determine SSL settings based on protocol
        ssl_enabled = protocol in ("https", "mtls")
        verify_mode = "CERT_REQUIRED" if protocol == "mtls" else "CERT_NONE"

        # Base configuration with all fields
        config: Dict[str, Any] = {
            "server": {
                "host": host,  # Default value
                "port": port,  # Default value
            },
            "client": {
                "timeout": 30.0,
            },
            "protocol": protocol,  # Always present
            "auth": {
                "method": "none",
                "api_key": {
                    "key": token,  # Optional, can be null
                    "header": "X-API-Key",
                },
                "certificate": {
                    "enabled": protocol == "mtls",
                    "cert_file": cert_file if protocol == "mtls" else None,
                    "key_file": key_file if protocol == "mtls" else None,
                    "ca_cert_file": ca_cert_file if protocol == "mtls" else None,
                },
            },
            "ssl": {
                "enabled": ssl_enabled,
                "verify": protocol != "http",
                "verify_mode": verify_mode,
                "check_hostname": False,
                "check_expiry": False,
                "cert_file": cert_file if ssl_enabled else None,
                "key_file": key_file if ssl_enabled else None,
                "ca_cert_file": ca_cert_file if ssl_enabled else None,
                "crl_file": crl_file,  # Optional, can be null
                "client_cert_required": protocol == "mtls",
            },
            "security": {
                "enabled": False,
            },
        }

        return config

    def generate_http_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        token: Optional[str] = None,
        crl_file: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Generate HTTP configuration without authentication.

        Args:
            host: Server host (default value)
            port: Server port (default value)
            token: Optional token (not used for HTTP, but included in config)
            crl_file: Optional CRL file
            output_path: Optional output file path

        Returns:
            Complete configuration dictionary with all fields
        """
        config = self._create_base_config(
            host=host,
            port=port,
            protocol="http",
            token=token,
            crl_file=crl_file,
        )
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_http_token_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        crl_file: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Generate HTTP configuration with token authentication.

        Args:
            host: Server host (default value)
            port: Server port (default value)
            api_key: API key for authentication (deprecated, use token)
            token: Authentication token
            crl_file: Optional CRL file
            output_path: Optional output file path

        Returns:
            Complete configuration dictionary with all fields
        """
        token_value = token or api_key or self.default_tokens["user"]
        config = self._create_base_config(
            host=host,
            port=port,
            protocol="http",
            token=token_value,
            crl_file=crl_file,
        )
        config["auth"]["method"] = "api_key"
        config["auth"]["api_key"]["key"] = token_value
        config["security"]["enabled"] = True
        config["security"]["tokens"] = {"user": token_value}
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_http_token_roles_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        tokens: Optional[Dict[str, str]] = None,
        roles: Optional[Dict[str, List[str]]] = None,
        crl_file: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Generate HTTP configuration with token authentication and roles.

        Args:
            host: Server host (default value)
            port: Server port (default value)
            api_key: API key for authentication (deprecated, use token)
            token: Authentication token
            tokens: Dictionary of tokens for different roles
            roles: Dictionary of roles and their permissions
            crl_file: Optional CRL file
            output_path: Optional output file path

        Returns:
            Complete configuration dictionary with all fields
        """
        tokens_dict = tokens or self.default_tokens
        roles_dict = roles or self.default_roles
        token_value = token or api_key or tokens_dict.get("admin", "admin-secret-key")
        config = self._create_base_config(
            host=host,
            port=port,
            protocol="http",
            token=token_value,
            crl_file=crl_file,
        )
        config["auth"]["method"] = "api_key"
        config["auth"]["api_key"]["key"] = token_value
        config["security"]["enabled"] = True
        config["security"]["tokens"] = tokens_dict
        config["security"]["roles"] = roles_dict
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_https_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        token: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        crl_file: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Generate HTTPS configuration without authentication.

        Args:
            host: Server host (default value)
            port: Server port (default value)
            token: Optional token (not used, but included in config)
            cert_file: Optional client certificate file
            key_file: Optional client key file
            ca_cert_file: Optional CA certificate file
            crl_file: Optional CRL file
            output_path: Optional output file path

        Returns:
            Complete configuration dictionary with all fields
        """
        config = self._create_base_config(
            host=host,
            port=port,
            protocol="https",
            token=token,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            crl_file=crl_file,
        )
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_https_token_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        crl_file: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Generate HTTPS configuration with token authentication.

        Args:
            host: Server host (default value)
            port: Server port (default value)
            api_key: API key for authentication (deprecated, use token)
            token: Authentication token
            cert_file: Optional client certificate file
            key_file: Optional client key file
            ca_cert_file: Optional CA certificate file
            crl_file: Optional CRL file
            output_path: Optional output file path

        Returns:
            Complete configuration dictionary with all fields
        """
        token_value = token or api_key or self.default_tokens["user"]
        config = self._create_base_config(
            host=host,
            port=port,
            protocol="https",
            token=token_value,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            crl_file=crl_file,
        )
        config["auth"]["method"] = "api_key"
        config["auth"]["api_key"]["key"] = token_value
        config["security"]["enabled"] = True
        config["security"]["tokens"] = {"user": token_value}
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_https_token_roles_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        tokens: Optional[Dict[str, str]] = None,
        roles: Optional[Dict[str, List[str]]] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        crl_file: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Generate HTTPS configuration with token authentication and roles.

        Args:
            host: Server host (default value)
            port: Server port (default value)
            api_key: API key for authentication (deprecated, use token)
            token: Authentication token
            tokens: Dictionary of tokens for different roles
            roles: Dictionary of roles and their permissions
            cert_file: Optional client certificate file
            key_file: Optional client key file
            ca_cert_file: Optional CA certificate file
            crl_file: Optional CRL file
            output_path: Optional output file path

        Returns:
            Complete configuration dictionary with all fields
        """
        tokens_dict = tokens or self.default_tokens
        roles_dict = roles or self.default_roles
        token_value = token or api_key or tokens_dict.get("admin", "admin-secret-key")
        config = self._create_base_config(
            host=host,
            port=port,
            protocol="https",
            token=token_value,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            crl_file=crl_file,
        )
        config["auth"]["method"] = "api_key"
        config["auth"]["api_key"]["key"] = token_value
        config["security"]["enabled"] = True
        config["security"]["tokens"] = tokens_dict
        config["security"]["roles"] = roles_dict
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_mtls_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        token: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        crl_file: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Generate mTLS configuration with client certificates.

        Args:
            host: Server host (default value)
            port: Server port (default value)
            token: Optional token (not used for mTLS, but included in config)
            cert_file: Client certificate file (required for mTLS)
            key_file: Client key file (required for mTLS)
            ca_cert_file: CA certificate file (required for mTLS)
            crl_file: Optional CRL file
            output_path: Optional output file path

        Returns:
            Complete configuration dictionary with all fields
        """
        config = self._create_base_config(
            host=host,
            port=port,
            protocol="mtls",
            token=token,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            crl_file=crl_file,
        )
        config["auth"]["method"] = "certificate"
        # For mTLS, certificates are required
        if cert_file:
            config["auth"]["certificate"]["cert_file"] = cert_file
        if key_file:
            config["auth"]["certificate"]["key_file"] = key_file
        if ca_cert_file:
            config["auth"]["certificate"]["ca_cert_file"] = ca_cert_file
        if output_path:
            self._save_config(config, output_path)
        return config

    def generate_mtls_roles_config(
        self,
        host: str = "localhost",
        port: int = 8001,
        token: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        crl_file: Optional[str] = None,
        roles: Optional[Dict[str, List[str]]] = None,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Generate mTLS configuration with client certificates and roles.

        Args:
            host: Server host (default value)
            port: Server port (default value)
            token: Optional token (not used for mTLS, but included in config)
            cert_file: Client certificate file (required for mTLS)
            key_file: Client key file (required for mTLS)
            ca_cert_file: CA certificate file (required for mTLS)
            crl_file: Optional CRL file
            roles: Dictionary of roles and their permissions
            output_path: Optional output file path

        Returns:
            Complete configuration dictionary with all fields
        """
        roles_dict = roles or self.default_roles
        config = self._create_base_config(
            host=host,
            port=port,
            protocol="mtls",
            token=token,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            crl_file=crl_file,
        )
        config["auth"]["method"] = "certificate"
        # For mTLS, certificates are required
        if cert_file:
            config["auth"]["certificate"]["cert_file"] = cert_file
        if key_file:
            config["auth"]["certificate"]["key_file"] = key_file
        if ca_cert_file:
            config["auth"]["certificate"]["ca_cert_file"] = ca_cert_file
        config["security"]["enabled"] = True
        config["security"]["roles"] = roles_dict
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
        crl_file: Optional[str] = None,
        token: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate all 8 security mode configurations.

        Args:
            host: Server host (default value for all configs)
            port: Server port (default value for all configs)
            output_dir: Optional output directory
            cert_file: Optional client certificate file
            key_file: Optional client key file
            ca_cert_file: Optional CA certificate file
            crl_file: Optional CRL file
            token: Optional authentication token

        Returns:
            Dictionary of all generated configurations
        """
        configs = {}

        # 1. HTTP
        configs["http"] = self.generate_http_config(
            host=host,
            port=port,
            token=token,
            crl_file=crl_file,
            output_path=output_dir / "http.json" if output_dir else None,
        )

        # 2. HTTP + Token
        configs["http_token"] = self.generate_http_token_config(
            host=host,
            port=port,
            token=token,
            crl_file=crl_file,
            output_path=output_dir / "http_token.json" if output_dir else None,
        )

        # 3. HTTP + Token + Roles
        configs["http_token_roles"] = self.generate_http_token_roles_config(
            host=host,
            port=port,
            token=token,
            crl_file=crl_file,
            output_path=output_dir / "http_token_roles.json" if output_dir else None,
        )

        # 4. HTTPS
        configs["https"] = self.generate_https_config(
            host=host,
            port=port,
            token=token,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            crl_file=crl_file,
            output_path=output_dir / "https.json" if output_dir else None,
        )

        # 5. HTTPS + Token
        configs["https_token"] = self.generate_https_token_config(
            host=host,
            port=port,
            token=token,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            crl_file=crl_file,
            output_path=output_dir / "https_token.json" if output_dir else None,
        )

        # 6. HTTPS + Token + Roles
        configs["https_token_roles"] = self.generate_https_token_roles_config(
            host=host,
            port=port,
            token=token,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            crl_file=crl_file,
            output_path=output_dir / "https_token_roles.json" if output_dir else None,
        )

        # 7. mTLS
        configs["mtls"] = self.generate_mtls_config(
            host=host,
            port=port,
            token=token,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            crl_file=crl_file,
            output_path=output_dir / "mtls.json" if output_dir else None,
        )

        # 8. mTLS + Roles
        configs["mtls_roles"] = self.generate_mtls_roles_config(
            host=host,
            port=port,
            token=token,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            crl_file=crl_file,
            output_path=output_dir / "mtls_roles.json" if output_dir else None,
        )

        return configs

    def _save_config(self, config: Dict[str, Any], output_path: Path) -> None:
        """Save configuration to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"Configuration saved to {output_path}")
