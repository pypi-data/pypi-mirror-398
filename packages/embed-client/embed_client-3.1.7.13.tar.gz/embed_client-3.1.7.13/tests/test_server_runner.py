#!/usr/bin/env python3
"""
Test Server Runner using MCP Proxy Adapter Framework
Runs test servers for all security modes using the framework's capabilities.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the framework to the path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent / ".venv" / "lib" / "python3.12" / "site-packages"),
)

try:
    from mcp_proxy_adapter.core.app_factory import create_and_run_server
    from mcp_proxy_adapter.config import Config

    FRAMEWORK_AVAILABLE = True
except ImportError:
    FRAMEWORK_AVAILABLE = False
    print("Warning: MCP Proxy Adapter framework not available.")


class TestServerRunner:
    """Test server runner using MCP Proxy Adapter framework."""

    def __init__(self):
        self.servers = {}
        self.configs_dir = Path(__file__).parent.parent / "configs"
        self.logger = logging.getLogger(__name__)

    def create_test_configs(self) -> Dict[str, str]:
        """Create test configurations for all security modes."""
        configs = {}

        # HTTP configurations
        http_configs = {
            "http_simple": {
                "uuid": "test-http-simple",
                "server": {"host": "localhost", "port": 10001, "protocol": "http"},
                "auth": {"method": "none"},
                "ssl": {"enabled": False},
                "security": {"enabled": False},
                "transport": {"verify_client": False, "chk_hostname": False},
                "logging": {"level": "INFO", "console_output": True},
            },
            "http_token": {
                "uuid": "test-http-token",
                "server": {"host": "localhost", "port": 10002, "protocol": "http"},
                "auth": {"method": "api_key"},
                "ssl": {"enabled": False},
                "security": {
                    "enabled": True,
                    "tokens": {"admin": "admin-secret-key", "user": "user-secret-key"},
                },
                "transport": {"verify_client": False, "chk_hostname": False},
                "logging": {"level": "INFO", "console_output": True},
            },
            "http_token_roles": {
                "uuid": "test-http-token-roles",
                "server": {"host": "localhost", "port": 10003, "protocol": "http"},
                "auth": {"method": "api_key"},
                "ssl": {"enabled": False},
                "security": {
                    "enabled": True,
                    "tokens": {
                        "admin": "admin-secret-key",
                        "user": "user-secret-key",
                        "readonly": "readonly-secret-key",
                    },
                    "roles": {
                        "admin": ["read", "write", "delete", "admin"],
                        "user": ["read", "write"],
                        "readonly": ["read"],
                    },
                },
                "transport": {"verify_client": False, "chk_hostname": False},
                "logging": {"level": "INFO", "console_output": True},
            },
        }

        # HTTPS configurations
        https_configs = {
            "https_simple": {
                "uuid": "test-https-simple",
                "server": {"host": "localhost", "port": 10011, "protocol": "https"},
                "auth": {"method": "none"},
                "ssl": {
                    "enabled": True,
                    "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
                    "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
                },
                "security": {"enabled": False},
                "transport": {"verify_client": False, "chk_hostname": False},
                "logging": {"level": "INFO", "console_output": True},
            },
            "https_token": {
                "uuid": "test-https-token",
                "server": {"host": "localhost", "port": 10012, "protocol": "https"},
                "auth": {"method": "api_key"},
                "ssl": {
                    "enabled": True,
                    "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
                    "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
                },
                "security": {
                    "enabled": True,
                    "tokens": {"admin": "admin-secret-key", "user": "user-secret-key"},
                },
                "transport": {"verify_client": False, "chk_hostname": False},
                "logging": {"level": "INFO", "console_output": True},
            },
            "https_token_roles": {
                "uuid": "test-https-token-roles",
                "server": {"host": "localhost", "port": 10013, "protocol": "https"},
                "auth": {"method": "api_key"},
                "ssl": {
                    "enabled": True,
                    "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
                    "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
                },
                "security": {
                    "enabled": True,
                    "tokens": {
                        "admin": "admin-secret-key",
                        "user": "user-secret-key",
                        "readonly": "readonly-secret-key",
                    },
                    "roles": {
                        "admin": ["read", "write", "delete", "admin"],
                        "user": ["read", "write"],
                        "readonly": ["read"],
                    },
                },
                "transport": {"verify_client": False, "chk_hostname": False},
                "logging": {"level": "INFO", "console_output": True},
            },
        }

        # mTLS configurations
        mtls_configs = {
            "mtls_simple": {
                "uuid": "test-mtls-simple",
                "server": {"host": "localhost", "port": 10021, "protocol": "mtls"},
                "auth": {"method": "certificate"},
                "ssl": {
                    "enabled": True,
                    "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
                    "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
                    "ca_cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/ca/ca.crt",
                },
                "security": {"enabled": False},
                "transport": {"verify_client": True, "chk_hostname": True},
                "logging": {"level": "INFO", "console_output": True},
            },
            "mtls_roles": {
                "uuid": "test-mtls-roles",
                "server": {"host": "localhost", "port": 10022, "protocol": "mtls"},
                "auth": {"method": "certificate"},
                "ssl": {
                    "enabled": True,
                    "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
                    "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
                    "ca_cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/ca/ca.crt",
                },
                "security": {
                    "enabled": True,
                    "roles": {
                        "admin": ["read", "write", "delete", "admin"],
                        "user": ["read", "write"],
                        "readonly": ["read"],
                    },
                },
                "transport": {"verify_client": True, "chk_hostname": True},
                "logging": {"level": "INFO", "console_output": True},
            },
        }

        # Combine all configurations
        all_configs = {**http_configs, **https_configs, **mtls_configs}

        # Save configurations
        for name, config in all_configs.items():
            config_path = self.configs_dir / f"test_{name}.json"
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            configs[name] = str(config_path)
            print(f"✅ Created config: {config_path}")

        return configs

    async def start_server(self, config_path: str, mode: str) -> bool:
        """Start a test server using the framework."""
        if not FRAMEWORK_AVAILABLE:
            print(f"❌ Framework not available for {mode}")
            return False

        try:
            print(f"🚀 Starting {mode} server with config: {config_path}")

            # Use the framework's app factory
            await create_and_run_server(
                config_path=config_path,
                title=f"Test Server - {mode}",
                description=f"Test server for {mode} security mode",
                version="1.0.0",
                host="localhost",
                log_level="info",
            )
            return True

        except Exception as e:
            print(f"❌ Failed to start {mode} server: {e}")
            return False

    async def start_server_background(self, config_path: str, mode: str) -> bool:
        """Start a test server in background using subprocess."""
        try:
            print(f"🚀 Starting {mode} server in background: {config_path}")

            # Start server using the framework's main module
            process = subprocess.Popen(
                [sys.executable, "-m", "mcp_proxy_adapter", "--config", config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.servers[mode] = process

            # Wait a bit for server to start
            await asyncio.sleep(2)

            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {mode} server started successfully (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {mode} server failed to start")
                print(f"STDOUT: {stdout.decode()}")
                print(f"STDERR: {stderr.decode()}")
                return False

        except Exception as e:
            print(f"❌ Failed to start {mode} server in background: {e}")
            return False

    async def stop_server(self, mode: str) -> bool:
        """Stop a test server."""
        if mode not in self.servers:
            return True

        try:
            process = self.servers[mode]
            process.terminate()
            process.wait(timeout=5)
            del self.servers[mode]
            print(f"✅ {mode} server stopped")
            return True
        except Exception as e:
            print(f"❌ Failed to stop {mode} server: {e}")
            return False

    async def stop_all_servers(self):
        """Stop all test servers."""
        for mode in list(self.servers.keys()):
            await self.stop_server(mode)

    async def run_all_servers(self, background: bool = True):
        """Run all test servers."""
        print("🔧 Creating test configurations...")
        configs = self.create_test_configs()

        print(f"🚀 Starting {len(configs)} test servers...")

        for mode, config_path in configs.items():
            if background:
                success = await self.start_server_background(config_path, mode)
            else:
                success = await self.start_server(config_path, mode)

            if not success:
                print(f"⚠️ Failed to start {mode} server")

        print(f"✅ Started {len(self.servers)} servers")
        print("🛑 Press Ctrl+C to stop all servers")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping all servers...")
            await self.stop_all_servers()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Server Runner")
    parser.add_argument("--mode", help="Specific mode to run")
    parser.add_argument("--background", action="store_true", help="Run in background")
    parser.add_argument("--create-configs", action="store_true", help="Create configs only")

    args = parser.parse_args()

    runner = TestServerRunner()

    if args.create_configs:
        runner.create_test_configs()
        return 0

    if args.mode:
        # Run specific mode
        configs = runner.create_test_configs()
        if args.mode in configs:
            config_path = configs[args.mode]
            if args.background:
                await runner.start_server_background(config_path, args.mode)
            else:
                await runner.start_server(config_path, args.mode)
        else:
            print(f"❌ Unknown mode: {args.mode}")
            return 1
    else:
        # Run all servers
        await runner.run_all_servers(background=args.background)

    return 0


if __name__ == "__main__":
    asyncio.run(main())
