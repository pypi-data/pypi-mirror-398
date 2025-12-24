"""
Default configuration and helpers for embed-client ClientConfig.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "server": {
        "host": "localhost",
        "port": 8001,
        "base_url": "http://localhost:8001",
    },
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1,
    "auth": {
        "method": "none",  # none, api_key, jwt, certificate, basic
        "api_key": {"key": None, "header": "X-API-Key"},
        "jwt": {
            "username": None,
            "password": None,
            "secret": None,
            "expiry_hours": 24,
        },
        "certificate": {
            "enabled": False,
            "cert_file": None,
            "key_file": None,
            "ca_cert_file": None,
        },
        "basic": {"username": None, "password": None},
    },
    "ssl": {
        "enabled": False,
        "verify": True,
        "check_hostname": True,
        "cert_file": None,
        "key_file": None,
        "ca_cert_file": None,
        "client_cert_required": False,
    },
    "security": {"enabled": False, "roles_enabled": False, "roles_file": None},
    "logging": {
        "enabled": False,
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
    "client": {"timeout": 30.0},
}


def update_nested_dict(
    target: Dict[str, Any], updates: Dict[str, Any]
) -> Dict[str, Any]:
    """Recursively update a nested dictionary in place.

    Args:
        target: Dictionary to update.
        updates: Dictionary with new values.

    Returns:
        The updated dictionary (same instance as ``target``).
    """
    for key, value in updates.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            update_nested_dict(target[key], value)
        else:
            target[key] = value
    return target


__all__ = ["DEFAULT_CONFIG", "update_nested_dict"]
