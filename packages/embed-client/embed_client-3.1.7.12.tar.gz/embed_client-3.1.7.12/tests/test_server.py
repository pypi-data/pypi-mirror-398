#!/usr/bin/env python3
"""
Test Server for Embedding Service
Simple test server that mimics the real embedding service endpoints
for testing all security modes.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import logging
import ssl
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import hypercorn.asyncio
from hypercorn import Config as HypercornConfig

# Import security framework components
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
    print("Warning: mcp_security_framework not available. Using basic server.")


# Request/Response models
class EmbedRequest(BaseModel):
    texts: List[str]
    model: Optional[str] = "default"
    dimensions: Optional[int] = None


class EmbedResponse(BaseModel):
    success: bool
    embeddings: List[List[float]]
    model: str
    dimensions: int
    count: int


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    security_mode: str


class CommandsResponse(BaseModel):
    commands: List[str]


class TestServer:
    """Test server that mimics embedding service endpoints."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app = FastAPI(
            title="Test Embedding Service",
            description="Test server for embedding service with security support",
            version="1.0.0",
        )
        self.security_manager = None
        self.setup_security()
        self.setup_routes()

    def setup_security(self):
        """Setup security manager if available."""
        if not SECURITY_FRAMEWORK_AVAILABLE:
            return

        try:
            # Extract security configuration from the new format
            security_section = self.config.get("security", {})
            transport_section = self.config.get("transport", {})

            # Determine authentication method
            auth_method = "none"
            if security_section.get("enabled", False):
                if security_section.get("tokens"):
                    auth_method = "api_key"
                elif security_section.get("roles"):
                    auth_method = "certificate"  # For mTLS with roles

            # Create security configuration
            security_config = SecurityConfig(
                auth=AuthConfig(
                    method=auth_method,
                    api_keys=security_section.get("tokens", {}),
                    jwt={},  # Not used in this example
                    basic={},  # Not used in this example
                    certificate={},  # Will be set from SSL config
                ),
                ssl=SSLConfig(
                    enabled=transport_section.get("verify_client", False),
                    verify_mode=("CERT_REQUIRED" if transport_section.get("verify_client", False) else "CERT_NONE"),
                    check_hostname=transport_section.get("chk_hostname", False),
                    check_expiry=True,
                    cert_file=self.config.get("ssl", {}).get("cert_file"),
                    key_file=self.config.get("ssl", {}).get("key_file"),
                    ca_cert_file=self.config.get("ssl", {}).get("ca_cert_file"),
                ),
            )

            self.security_manager = SecurityManager(security_config)
            logging.info("Security manager initialized")
        except Exception as e:
            logging.warning(f"Failed to initialize security manager: {e}")

    def setup_routes(self):
        """Setup API routes."""

        @self.app.get("/health", response_model=HealthResponse)
        async def health():
            """Health check endpoint."""
            return HealthResponse(
                status="ok",
                timestamp=str(asyncio.get_event_loop().time()),
                version="1.0.0",
                security_mode=self.config.get("auth", {}).get("method", "none"),
            )

        @self.app.get("/openapi.json")
        async def openapi_schema():
            """OpenAPI schema endpoint."""
            return {
                "openapi": "3.0.0",
                "info": {
                    "title": "Test Embedding Service",
                    "version": "1.0.0",
                    "description": "Test server for embedding service",
                },
                "paths": {
                    "/health": {
                        "get": {
                            "summary": "Health check",
                            "responses": {"200": {"description": "OK"}},
                        }
                    },
                    "/embed": {
                        "post": {
                            "summary": "Generate embeddings",
                            "responses": {"200": {"description": "OK"}},
                        }
                    },
                },
            }

        @self.app.get("/api/commands", response_model=CommandsResponse)
        async def get_commands():
            """Get available commands."""
            return CommandsResponse(commands=["embed", "health", "openapi.json"])

        @self.app.post("/embed", response_model=EmbedResponse)
        async def embed_texts(request: EmbedRequest, http_request: Request):
            """Generate embeddings for texts."""
            # Check authentication if enabled
            if self.security_manager:
                try:
                    # Extract authentication from headers or certificates
                    auth_result = await self.security_manager.validate_request(http_request)
                    if not auth_result.success:
                        raise HTTPException(status_code=401, detail="Authentication failed")
                except Exception as e:
                    raise HTTPException(status_code=401, detail=f"Authentication error: {e}")

            # Generate mock embeddings
            embeddings = []
            for text in request.texts:
                # Create a simple mock embedding based on text length and content
                embedding = [float(ord(c) % 100) / 100.0 for c in text[: request.dimensions or 384]]
                # Pad or truncate to desired dimensions
                target_dim = request.dimensions or 384
                if len(embedding) < target_dim:
                    embedding.extend([0.0] * (target_dim - len(embedding)))
                else:
                    embedding = embedding[:target_dim]
                embeddings.append(embedding)

            return EmbedResponse(
                success=True,
                embeddings=embeddings,
                model=request.model,
                dimensions=len(embeddings[0]) if embeddings else 0,
                count=len(embeddings),
            )

        @self.app.post("/cmd")
        async def cmd_endpoint(request: Dict[str, Any], http_request: Request):
            """Generic command endpoint (JSON-RPC style)."""
            # Check authentication if enabled
            if self.security_manager:
                try:
                    auth_result = await self.security_manager.validate_request(http_request)
                    if not auth_result.success:
                        raise HTTPException(status_code=401, detail="Authentication failed")
                except Exception as e:
                    raise HTTPException(status_code=401, detail=f"Authentication error: {e}")

            command = request.get("command")
            params = request.get("params", {})

            if command == "embed":
                texts = params.get("texts", [])
                if not texts:
                    raise HTTPException(status_code=400, detail="No texts provided")

                # Generate mock embeddings
                embeddings = []
                for text in texts:
                    embedding = [float(ord(c) % 100) / 100.0 for c in text[:384]]
                    if len(embedding) < 384:
                        embedding.extend([0.0] * (384 - len(embedding)))
                    embeddings.append(embedding)

                return {
                    "success": True,
                    "result": {"data": [{"embedding": emb, "index": i} for i, emb in enumerate(embeddings)]},
                }

            elif command == "health":
                return {
                    "success": True,
                    "result": {
                        "status": "ok",
                        "timestamp": str(asyncio.get_event_loop().time()),
                        "version": "1.0.0",
                    },
                }

            elif command == "help":
                return {
                    "success": True,
                    "result": {
                        "message": "Available commands: embed, health, help",
                        "commands": ["embed", "health", "help"],
                    },
                }

            else:
                raise HTTPException(status_code=400, detail=f"Unknown command: {command}")


def create_ssl_context(config: Dict[str, Any]) -> Optional[ssl.SSLContext]:
    """Create SSL context for the server."""
    if not config.get("ssl", {}).get("enabled", False):
        return None

    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        # Load server certificate and key
        cert_file = config.get("ssl", {}).get("cert_file")
        key_file = config.get("ssl", {}).get("key_file")

        if cert_file and key_file:
            context.load_cert_chain(cert_file, key_file)

        # Load CA certificate if provided
        ca_cert_file = config.get("ssl", {}).get("ca_cert_file")
        if ca_cert_file:
            context.load_verify_locations(ca_cert_file)

        # Configure verification
        verify_mode = config.get("ssl", {}).get("verify_mode", "CERT_NONE")
        if verify_mode == "CERT_NONE":
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        elif verify_mode == "CERT_OPTIONAL":
            context.verify_mode = ssl.CERT_OPTIONAL
        elif verify_mode == "CERT_REQUIRED":
            context.verify_mode = ssl.CERT_REQUIRED
            context.check_hostname = config.get("ssl", {}).get("check_hostname", True)

        return context
    except Exception as e:
        logging.error(f"Failed to create SSL context: {e}")
        return None


async def run_test_server(config: Dict[str, Any], host: str = "localhost", port: int = 10001):
    """Run the test server."""
    server = TestServer(config)

    # Create SSL context if needed
    ssl_context = create_ssl_context(config)

    # Configure hypercorn
    hypercorn_config = HypercornConfig()
    hypercorn_config.bind = [f"{host}:{port}"]
    hypercorn_config.ssl_context = ssl_context
    hypercorn_config.loglevel = "info"

    print(f"🚀 Starting test server on {host}:{port}")
    print(f"🔒 Security mode: {config.get('security', {}).get('enabled', False)}")
    print(f"🔐 SSL enabled: {config.get('ssl', {}).get('enabled', False)}")

    await hypercorn.asyncio.serve(server.app, hypercorn_config)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Embedding Service Server")
    parser.add_argument("--config", "-c", required=True, help="Path to configuration file")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8001, help="Server port")

    args = parser.parse_args()

    # Load configuration
    with open(args.config, "r") as f:
        config = json.load(f)

    # Run server
    asyncio.run(run_test_server(config, args.host, args.port))


if __name__ == "__main__":
    main()
