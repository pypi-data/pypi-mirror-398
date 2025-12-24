#!/usr/bin/env python3
"""
HTTPS Test Server
Test server with SSL/TLS support for HTTPS and mTLS testing.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import logging
import ssl
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp_security_framework import (
        SecurityManager,
        SecurityConfig,
        AuthConfig,
        SSLConfig,
    )

    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError:
    SECURITY_FRAMEWORK_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbedRequest(BaseModel):
    texts: list[str]


class HTTPServer:
    """HTTPS test server with SSL/TLS support."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app = FastAPI(title="HTTPS Test Server", version="1.0.0")
        self.security_manager = None
        self.setup_routes()
        self.setup_security()

    def setup_routes(self):
        """Setup API routes."""

        @self.app.get("/health")
        async def health():
            return {
                "status": "ok",
                "timestamp": "990.666509752",
                "version": "1.0.0",
                "security_mode": ("https" if self.config.get("ssl", {}).get("enabled", False) else "none"),
            }

        @self.app.get("/openapi.json")
        async def openapi():
            return self.app.openapi()

        @self.app.get("/commands")
        async def commands():
            return {"commands": ["health", "help", "embed"]}

        @self.app.post("/cmd/help")
        async def help_cmd():
            return {
                "help": "Available commands: health, help, embed",
                "usage": "Use POST /cmd/{command} for commands",
            }

        @self.app.post("/cmd/embed")
        async def embed_cmd(request: EmbedRequest):
            # Generate mock embeddings
            embeddings = []
            for text in request.texts:
                # Generate a simple mock embedding (512 dimensions)
                embedding = [0.1] * 512
                embeddings.append(embedding)

            return {"embeddings": embeddings, "count": len(embeddings)}

    def setup_security(self):
        """Setup security manager if available."""
        if not SECURITY_FRAMEWORK_AVAILABLE:
            return

        try:
            # Extract security configuration
            security_section = self.config.get("security", {})
            ssl_section = self.config.get("ssl", {})
            transport_section = self.config.get("transport", {})

            # Determine authentication method
            auth_method = "none"
            if security_section.get("enabled", False):
                if security_section.get("tokens"):
                    auth_method = "api_key"
                elif security_section.get("roles"):
                    auth_method = "certificate"

            # Create security configuration
            security_config = SecurityConfig(
                auth=AuthConfig(
                    method=auth_method,
                    api_keys=security_section.get("tokens", {}),
                    jwt={},
                    basic={},
                    certificate={},
                ),
                ssl=SSLConfig(
                    enabled=ssl_section.get("enabled", False),
                    verify_mode=("CERT_REQUIRED" if transport_section.get("verify_client", False) else "CERT_NONE"),
                    check_hostname=transport_section.get("chk_hostname", False),
                    check_expiry=True,
                    cert_file=ssl_section.get("cert_file"),
                    key_file=ssl_section.get("key_file"),
                    ca_cert_file=ssl_section.get("ca_cert_file"),
                ),
            )

            self.security_manager = SecurityManager(security_config)
            logger.info("Security manager initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize security manager: {e}")

    def create_ssl_context(self):
        """Create SSL context for HTTPS/mTLS."""
        ssl_config = self.config.get("ssl", {})
        transport_config = self.config.get("transport", {})

        if not ssl_config.get("enabled", False):
            return None

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        # Load server certificate and key
        cert_file = ssl_config.get("cert_file") or transport_config.get("cert_file")
        key_file = ssl_config.get("key_file") or transport_config.get("key_file")

        if cert_file and key_file:
            context.load_cert_chain(cert_file, key_file)

        # Load CA certificate for client verification (mTLS)
        if transport_config.get("verify_client", False):
            ca_cert_file = ssl_config.get("ca_cert_file") or transport_config.get("ca_cert_file")
            if ca_cert_file:
                context.load_verify_locations(ca_cert_file)
                context.verify_mode = ssl.CERT_REQUIRED
                context.check_hostname = transport_config.get("chk_hostname", True)

        return context

    async def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the HTTPS server."""
        ssl_context = self.create_ssl_context()

        if ssl_context:
            logger.info(f"🚀 Starting HTTPS server on {host}:{port}")
            logger.info("🔐 SSL/TLS enabled")
        else:
            logger.info(f"🚀 Starting HTTP server on {host}:{port}")
            logger.info("🔓 SSL/TLS disabled")

        config = uvicorn.Config(app=self.app, host=host, port=port, log_level="info")

        if ssl_context:
            config.ssl_keyfile = self.config.get("ssl", {}).get("key_file") or self.config.get("transport", {}).get(
                "key_file"
            )
            config.ssl_certfile = self.config.get("ssl", {}).get("cert_file") or self.config.get("transport", {}).get(
                "cert_file"
            )

        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="HTTPS Test Server")
    parser.add_argument("--config", required=True, help="Configuration file")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")

    args = parser.parse_args()

    # Load configuration
    with open(args.config, "r") as f:
        config = json.load(f)

    # Create and run server
    server = HTTPServer(config)
    await server.run(args.host, args.port)


if __name__ == "__main__":
    asyncio.run(main())
