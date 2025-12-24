"""
Configuration Validator for embed-client.

Validates client configuration files for correctness, completeness,
and consistency across all security modes.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from embed_client.config import ClientConfig
from embed_client.config_presets import validate_client_config


class ConfigValidator:
    """
    Validator for embed-client configuration files.

    Provides comprehensive validation of configuration structure,
    required fields, file paths, and security settings.
    """

    def __init__(self) -> None:
        """Initialize configuration validator."""
        pass

    def validate_json_structure(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate JSON structure and required fields.

        Args:
            config_data: Configuration dictionary

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: List[str] = []

        # Check required top-level sections
        required_sections = ["server"]
        for section in required_sections:
            if section not in config_data:
                errors.append(f"Missing required section: {section}")

        # Validate server section
        if "server" in config_data:
            server = config_data["server"]
            if "host" not in server:
                errors.append("server.host is required")
            if "port" not in server:
                errors.append("server.port is required")
            elif not isinstance(server["port"], int) or server["port"] <= 0:
                errors.append("server.port must be a positive integer")

        # Validate auth section (if present)
        if "auth" in config_data:
            auth = config_data["auth"]
            auth_method = auth.get("method", "none")

            if auth_method == "api_key":
                if "api_key" not in auth or "key" not in auth["api_key"]:
                    errors.append("auth.api_key.key is required for api_key authentication")
            elif auth_method == "jwt":
                jwt = auth.get("jwt", {})
                if not all(key in jwt for key in ["username", "password", "secret"]):
                    errors.append(
                        "auth.jwt.username, auth.jwt.password, and auth.jwt.secret "
                        "are required for JWT authentication"
                    )
            elif auth_method == "certificate":
                cert = auth.get("certificate", {})
                if not all(key in cert for key in ["cert_file", "key_file"]):
                    errors.append(
                        "auth.certificate.cert_file and auth.certificate.key_file "
                        "are required for certificate authentication"
                    )
            elif auth_method == "basic":
                basic = auth.get("basic", {})
                if not all(key in basic for key in ["username", "password"]):
                    errors.append(
                        "auth.basic.username and auth.basic.password "
                        "are required for basic authentication"
                    )

        # Validate protocol field (if present)
        protocol = config_data.get("protocol", "http")
        if protocol not in ("http", "https", "mtls"):
            errors.append(f"Invalid protocol: {protocol}. Must be 'http', 'https', or 'mtls'")

        # Validate SSL section (if present)
        if "ssl" in config_data:
            ssl = config_data["ssl"]
            if ssl.get("enabled", False):
                cert_file = ssl.get("cert_file")
                key_file = ssl.get("key_file")
                ca_cert_file = ssl.get("ca_cert_file")
                crl_file = ssl.get("crl_file")

                # For mTLS, certificates are required
                if protocol == "mtls":
                    if not cert_file:
                        errors.append("SSL certificate file is required for mTLS protocol")
                    elif not os.path.exists(cert_file):
                        errors.append(f"SSL certificate file not found: {cert_file}")
                    
                    if not key_file:
                        errors.append("SSL key file is required for mTLS protocol")
                    elif not os.path.exists(key_file):
                        errors.append(f"SSL key file not found: {key_file}")
                    
                    if not ca_cert_file:
                        errors.append("SSL CA certificate file is required for mTLS protocol")
                    elif not os.path.exists(ca_cert_file):
                        errors.append(f"SSL CA certificate file not found: {ca_cert_file}")
                else:
                    # For HTTPS, certificates are optional but should exist if specified
                    if cert_file and not os.path.exists(cert_file):
                        errors.append(f"SSL certificate file not found: {cert_file}")
                    if key_file and not os.path.exists(key_file):
                        errors.append(f"SSL key file not found: {key_file}")
                    if ca_cert_file and not os.path.exists(ca_cert_file):
                        errors.append(f"SSL CA certificate file not found: {ca_cert_file}")
                
                # CRL is always optional
                if crl_file and not os.path.exists(crl_file):
                    errors.append(f"SSL CRL file not found: {crl_file}")

        return len(errors) == 0, errors

    def validate_config_file(
        self, config_path: Path
    ) -> Tuple[bool, str, List[str]]:
        """
        Validate a single configuration file.

        Args:
            config_path: Path to configuration file

        Returns:
            Tuple of (is_valid, status_message, list_of_errors)
        """
        try:
            if not config_path.exists():
                return False, "File not found", []

            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Validate JSON structure
            is_valid, errors = self.validate_json_structure(config_data)

            if not is_valid:
                return False, f"{len(errors)} error(s) in structure", errors

            # Validate using ClientConfig validator
            try:
                client_config = ClientConfig(str(config_path))
                config_errors = validate_client_config(client_config)

                if config_errors:
                    errors.extend(config_errors)
                    return False, f"{len(errors)} error(s) found", errors

                return True, "OK", []
            except Exception as e:
                errors.append(f"Error loading config: {str(e)}")
                return False, f"Config loading failed: {str(e)}", errors

        except json.JSONDecodeError as e:
            return False, f"JSON decode error: {str(e)}", []
        except Exception as e:
            return False, f"Unexpected error: {str(e)}", []

    def validate_config_dict(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate configuration dictionary.

        Args:
            config_data: Configuration dictionary

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        # Validate JSON structure
        is_valid, errors = self.validate_json_structure(config_data)

        if not is_valid:
            return False, errors

        # Create temporary ClientConfig to validate
        try:
            # Create a temporary config file
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(config_data, f, indent=2)
                temp_path = f.name

            try:
                client_config = ClientConfig(temp_path)
                config_errors = validate_client_config(client_config)
                if config_errors:
                    errors.extend(config_errors)
                    return False, errors
                return True, []
            finally:
                os.unlink(temp_path)
        except Exception as e:
            errors.append(f"Error validating config: {str(e)}")
            return False, errors

    def validate_config_directory(self, config_dir: Path) -> Dict[str, Tuple[bool, str, List[str]]]:
        """
        Validate all configuration files in a directory.

        Args:
            config_dir: Directory containing configuration files

        Returns:
            Dictionary mapping file names to (is_valid, status_message, list_of_errors)
        """
        results: Dict[str, Tuple[bool, str, List[str]]] = {}

        if not config_dir.exists():
            return results

        config_files = list(config_dir.glob("*.json"))

        for config_file in sorted(config_files):
            results[config_file.name] = self.validate_config_file(config_file)

        return results


__all__ = ["ConfigValidator"]

