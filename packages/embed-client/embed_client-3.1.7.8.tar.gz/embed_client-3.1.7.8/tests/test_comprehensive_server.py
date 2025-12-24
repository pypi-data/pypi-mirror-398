#!/usr/bin/env python3
"""
Comprehensive Test Server for All Security Modes
Test server that supports all security modes using MCP Proxy Adapter framework:
- HTTP (no auth, with token, with roles)
- HTTPS (no auth, with token, with roles) 
- mTLS (no auth, with roles)

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import logging
import ssl
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add the framework to the path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent / ".venv" / "lib" / "python3.12" / "site-packages"),
)

try:
    from mcp_proxy_adapter.core.app_factory import create_and_run_server
    from mcp_proxy_adapter.api.app import create_app
    from mcp_proxy_adapter.config import Config

    FRAMEWORK_AVAILABLE = True
except ImportError:
    FRAMEWORK_AVAILABLE = False
    print("Warning: MCP Proxy Adapter framework not available. Using basic server.")


class ComprehensiveTestServer:
    """Comprehensive test server supporting all security modes."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load_config()
        self.server = None
        self.thread = None
        self.logger = logging.getLogger(__name__)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        with open(self.config_path, "r") as f:
            return json.load(f)

    def create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context based on configuration."""
        ssl_config = self.config.get("ssl", {})

        if not ssl_config.get("enabled", False):
            return None

        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

            # Load server certificate and key
            cert_file = ssl_config.get("cert_file")
            key_file = ssl_config.get("key_file")

            if cert_file and key_file:
                context.load_cert_chain(cert_file, key_file)

            # Load CA certificate for client verification
            ca_cert_file = ssl_config.get("ca_cert_file")
            if ca_cert_file:
                context.load_verify_locations(ca_cert_file)

            # Configure verification mode
            verify_mode = ssl_config.get("verify_mode", "CERT_NONE")
            if verify_mode == "CERT_REQUIRED":
                context.verify_mode = ssl.CERT_REQUIRED
                context.check_hostname = ssl_config.get("check_hostname", True)
            elif verify_mode == "CERT_OPTIONAL":
                context.verify_mode = ssl.CERT_OPTIONAL
            else:
                context.verify_mode = ssl.CERT_NONE
                context.check_hostname = False

            return context
        except Exception as e:
            self.logger.error(f"Failed to create SSL context: {e}")
            return None

    def get_security_info(self) -> Dict[str, Any]:
        """Get security configuration info."""
        security = self.config.get("security", {})
        transport = self.config.get("transport", {})

        return {
            "enabled": security.get("enabled", False),
            "auth_method": self.config.get("auth", {}).get("method", "none"),
            "tokens": bool(security.get("tokens")),
            "roles": bool(security.get("roles")),
            "mtls": transport.get("verify_client", False),
            "ssl_enabled": self.config.get("ssl", {}).get("enabled", False),
        }

    def start_server(self):
        """Start the test server."""
        server_config = self.config.get("server", {})
        host = server_config.get("host", "localhost")
        port = server_config.get("port", 8001)

        security_info = self.get_security_info()

        print(f"🚀 Starting Comprehensive Test Server")
        print(f"📁 Configuration: {self.config_path}")
        print(f"🌐 Server: {host}:{port}")
        print(f"🔐 Security: {'Enabled' if security_info['enabled'] else 'Disabled'}")
        print(f"🔑 Auth Method: {security_info['auth_method']}")
        print(f"🎫 Tokens: {'Enabled' if security_info['tokens'] else 'Disabled'}")
        print(f"👥 Roles: {'Enabled' if security_info['roles'] else 'Disabled'}")
        print(f"🔒 mTLS: {'Enabled' if security_info['mtls'] else 'Disabled'}")
        print(f"🔐 SSL: {'Enabled' if security_info['ssl_enabled'] else 'Disabled'}")

        if FRAMEWORK_AVAILABLE:
            print(f"🏗️ Using MCP Proxy Adapter Framework")
            try:
                # Use the framework to create and run server
                asyncio.run(
                    create_and_run_server(
                        config_path=self.config_path,
                        title="Comprehensive Test Server",
                        description="Test server for all security modes",
                        version="1.0.0",
                        host=host,
                        log_level="info",
                    )
                )
            except Exception as e:
                print(f"❌ Framework server failed: {e}")
                print(f"🔄 Falling back to basic server...")
                self._start_basic_server(host, port)
        else:
            print(f"⚠️ Framework not available, using basic server")
            self._start_basic_server(host, port)

    def _start_basic_server(self, host: str, port: int):
        """Start basic HTTP server as fallback."""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json

        class TestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/health":
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {
                        "status": "healthy",
                        "service": "comprehensive-test-server",
                        "version": "1.0.0",
                        "security_mode": self.server.security_info["auth_method"],
                        "timestamp": time.time(),
                    }
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_response(404)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {"error": "Not found", "path": self.path}
                    self.wfile.write(json.dumps(response).encode())

            def do_POST(self):
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length)

                try:
                    data = json.loads(post_data.decode())
                except json.JSONDecodeError:
                    data = {"raw": post_data.decode()}

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                response = {
                    "received": data,
                    "timestamp": time.time(),
                    "method": "POST",
                }
                self.wfile.write(json.dumps(response).encode())

        # Create server
        self.server = HTTPServer((host, port), TestHandler)
        self.server.security_info = self.get_security_info()

        # Configure SSL if needed
        ssl_context = self.create_ssl_context()
        if ssl_context:
            self.server.socket = ssl_context.wrap_socket(self.server.socket, server_side=True)

        print(f"✅ Basic Test Server started on {host}:{port}")
        print(f"📜 Available endpoints:")
        print(f"  - GET  /health - Health check")
        print(f"  - POST /       - Echo test")
        print(f"\n🛑 Press Ctrl+C to stop the server")

        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print(f"\n🛑 Server stopped by user")
            self.server.shutdown()

    def start_background(self):
        """Start server in background thread."""
        self.thread = threading.Thread(target=self.start_server, daemon=True)
        self.thread.start()
        time.sleep(2)  # Give server time to start
        return self.thread.is_alive()

    def stop_server(self):
        """Stop the server."""
        if self.server:
            self.server.shutdown()
        if self.thread:
            self.thread.join(timeout=5)


def create_test_configs():
    """Create test configurations for all security modes."""
    base_dir = Path(__file__).parent.parent / "configs"
    base_dir.mkdir(exist_ok=True)

    # HTTP configurations
    http_configs = {
        "http_simple": {
            "server": {"host": "localhost", "port": 10001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
            "security": {"enabled": False},
        },
        "http_token": {
            "server": {"host": "localhost", "port": 10002},
            "auth": {"method": "api_key"},
            "ssl": {"enabled": False},
            "security": {
                "enabled": True,
                "tokens": {"admin": "admin-secret-key", "user": "user-secret-key"},
            },
        },
        "http_token_roles": {
            "server": {"host": "localhost", "port": 10003},
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
        },
    }

    # HTTPS configurations
    https_configs = {
        "https_simple": {
            "server": {"host": "localhost", "port": 10011},
            "auth": {"method": "none"},
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
                "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
                "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
            },
            "security": {"enabled": False},
        },
        "https_token": {
            "server": {"host": "localhost", "port": 10012},
            "auth": {"method": "api_key"},
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
                "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
                "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
            },
            "security": {
                "enabled": True,
                "tokens": {"admin": "admin-secret-key", "user": "user-secret-key"},
            },
        },
        "https_token_roles": {
            "server": {"host": "localhost", "port": 10013},
            "auth": {"method": "api_key"},
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
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
        },
    }

    # mTLS configurations
    mtls_configs = {
        "mtls_simple": {
            "server": {"host": "localhost", "port": 10021},
            "auth": {"method": "certificate"},
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_REQUIRED",
                "check_hostname": True,
                "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
                "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
                "ca_cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/ca/ca.crt",
            },
            "transport": {"verify_client": True, "chk_hostname": True},
            "security": {"enabled": False},
        },
        "mtls_roles": {
            "server": {"host": "localhost", "port": 10022},
            "auth": {"method": "certificate"},
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_REQUIRED",
                "check_hostname": True,
                "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
                "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
                "ca_cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/ca/ca.crt",
            },
            "transport": {"verify_client": True, "chk_hostname": True},
            "security": {
                "enabled": True,
                "roles": {
                    "admin": ["read", "write", "delete", "admin"],
                    "user": ["read", "write"],
                    "readonly": ["read"],
                },
            },
        },
    }

    # Save all configurations
    all_configs = {**http_configs, **https_configs, **mtls_configs}

    for name, config in all_configs.items():
        config_path = base_dir / f"test_{name}.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Created config: {config_path}")

    return all_configs


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive Test Server")
    parser.add_argument("--config", "-c", help="Path to configuration file")
    parser.add_argument("--create-configs", action="store_true", help="Create test configurations")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--background", action="store_true", help="Run in background")

    args = parser.parse_args()

    if args.create_configs:
        print("🔧 Creating test configurations...")
        create_test_configs()
        return 0

    if not args.config:
        print("❌ Configuration file required. Use --config or --create-configs")
        return 1

    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return 1

    # Create and start server
    server = ComprehensiveTestServer(str(config_path))

    if args.background:
        print("🔄 Starting server in background...")
        if server.start_background():
            print("✅ Server started in background")
            print("💡 Use Ctrl+C to stop")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping background server...")
                server.stop_server()
        else:
            print("❌ Failed to start server in background")
            return 1
    else:
        server.start_server()

    return 0


if __name__ == "__main__":
    sys.exit(main())
