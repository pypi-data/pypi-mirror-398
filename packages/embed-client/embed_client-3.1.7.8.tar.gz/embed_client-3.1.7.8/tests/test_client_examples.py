#!/usr/bin/env python3
"""
Test Client Examples
Tests all security modes using embed-client examples.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add the framework to the path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent / ".venv" / "lib" / "python3.12" / "site-packages"),
)

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.client_factory import ClientFactory


class ClientExamplesTester:
    """Tester for all client examples."""

    def __init__(self):
        self.test_results = {}
        self.logger = logging.getLogger(__name__)

    async def test_http_plain(self):
        """Test HTTP plain mode."""
        print("🔍 Testing HTTP plain mode...")

        try:
            # Method 1: Direct client creation
            async with EmbeddingServiceAsyncClient("http://localhost", 10001) as client:
                print(f"✅ Client: {client.base_url}:{client.port}")
                print(f"✅ SSL enabled: {client.is_ssl_enabled()}")
                print(f"✅ Authenticated: {client.is_authenticated()}")

                # Test health check
                health = await client.health()
                print(f"✅ Health: {health}")

                # Test help command
                help_result = await client.cmd("help")
                print(f"✅ Help: {len(help_result)} keys in response")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts}
                embed_result = await client.cmd("embed", params=params)
                print(f"✅ Embed: {len(embed_result)} keys in response")

                return True

        except Exception as e:
            print(f"❌ HTTP plain test failed: {e}")
            return False

    async def test_http_token(self):
        """Test HTTP with token mode."""
        print("🔍 Testing HTTP token mode...")

        try:
            # Method 1: Using with_auth class method
            async with EmbeddingServiceAsyncClient.with_auth(
                "http://localhost", 10002, "api_key", api_key="admin-secret-key"
            ) as client:
                print(f"✅ Client: {client.base_url}:{client.port}")
                print(f"✅ SSL enabled: {client.is_ssl_enabled()}")
                print(f"✅ Authenticated: {client.is_authenticated()}")
                print(f"✅ Auth method: {client.get_auth_method()}")
                print(f"✅ Auth headers: {client.get_auth_headers()}")

                # Test health check
                health = await client.health()
                print(f"✅ Health: {health}")

                # Test help command
                help_result = await client.cmd("help")
                print(f"✅ Help: {len(help_result)} keys in response")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts}
                embed_result = await client.cmd("embed", params=params)
                print(f"✅ Embed: {len(embed_result)} keys in response")

                return True

        except Exception as e:
            print(f"❌ HTTP token test failed: {e}")
            return False

    async def test_https_plain(self):
        """Test HTTPS plain mode."""
        print("🔍 Testing HTTPS plain mode...")

        try:
            # Method 1: Direct client creation with HTTPS
            async with EmbeddingServiceAsyncClient("https://localhost", 10011) as client:
                print(f"✅ Client: {client.base_url}:{client.port}")
                print(f"✅ SSL enabled: {client.is_ssl_enabled()}")
                print(f"✅ Authenticated: {client.is_authenticated()}")

                # Test health check
                health = await client.health()
                print(f"✅ Health: {health}")

                # Test help command
                help_result = await client.cmd("help")
                print(f"✅ Help: {len(help_result)} keys in response")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts}
                embed_result = await client.cmd("embed", params=params)
                print(f"✅ Embed: {len(embed_result)} keys in response")

                return True

        except Exception as e:
            print(f"❌ HTTPS plain test failed: {e}")
            return False

    async def test_https_token(self):
        """Test HTTPS with token mode."""
        print("🔍 Testing HTTPS token mode...")

        try:
            # Method 1: Using with_auth class method
            async with EmbeddingServiceAsyncClient.with_auth(
                "https://localhost", 10012, "api_key", api_key="admin-secret-key"
            ) as client:
                print(f"✅ Client: {client.base_url}:{client.port}")
                print(f"✅ SSL enabled: {client.is_ssl_enabled()}")
                print(f"✅ Authenticated: {client.is_authenticated()}")
                print(f"✅ Auth method: {client.get_auth_method()}")
                print(f"✅ Auth headers: {client.get_auth_headers()}")

                # Test health check
                health = await client.health()
                print(f"✅ Health: {health}")

                # Test help command
                help_result = await client.cmd("help")
                print(f"✅ Help: {len(help_result)} keys in response")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts}
                embed_result = await client.cmd("embed", params=params)
                print(f"✅ Embed: {len(embed_result)} keys in response")

                return True

        except Exception as e:
            print(f"❌ HTTPS token test failed: {e}")
            return False

    async def test_mtls_plain(self):
        """Test mTLS plain mode."""
        print("🔍 Testing mTLS plain mode...")

        try:
            # Method 1: Using configuration dictionary
            config_dict = {
                "server": {"host": "https://localhost", "port": 10021},
                "auth": {"method": "certificate"},
                "ssl": {
                    "enabled": True,
                    "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/client/embedding-service.crt",
                    "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/client/embedding-service.key",
                    "ca_cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/ca/ca.crt",
                },
            }

            async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
                print(f"✅ Client: {client.base_url}:{client.port}")
                print(f"✅ SSL enabled: {client.is_ssl_enabled()}")
                print(f"✅ Authenticated: {client.is_authenticated()}")
                print(f"✅ Auth method: {client.get_auth_method()}")

                # Test health check
                health = await client.health()
                print(f"✅ Health: {health}")

                # Test help command
                help_result = await client.cmd("help")
                print(f"✅ Help: {len(help_result)} keys in response")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts}
                embed_result = await client.cmd("embed", params=params)
                print(f"✅ Embed: {len(embed_result)} keys in response")

                return True

        except Exception as e:
            print(f"❌ mTLS plain test failed: {e}")
            return False

    async def test_mtls_roles(self):
        """Test mTLS with roles mode."""
        print("🔍 Testing mTLS roles mode...")

        try:
            # Method 1: Using configuration dictionary
            config_dict = {
                "server": {"host": "https://localhost", "port": 10022},
                "auth": {"method": "certificate"},
                "ssl": {
                    "enabled": True,
                    "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/client/embedding-service.crt",
                    "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/client/embedding-service.key",
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
            }

            async with EmbeddingServiceAsyncClient(config_dict=config_dict) as client:
                print(f"✅ Client: {client.base_url}:{client.port}")
                print(f"✅ SSL enabled: {client.is_ssl_enabled()}")
                print(f"✅ Authenticated: {client.is_authenticated()}")
                print(f"✅ Auth method: {client.get_auth_method()}")

                # Test health check
                health = await client.health()
                print(f"✅ Health: {health}")

                # Test help command
                help_result = await client.cmd("help")
                print(f"✅ Help: {len(help_result)} keys in response")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts}
                embed_result = await client.cmd("embed", params=params)
                print(f"✅ Embed: {len(embed_result)} keys in response")

                return True

        except Exception as e:
            print(f"❌ mTLS roles test failed: {e}")
            return False

    async def test_real_server_8001(self):
        """Test real server on port 8001."""
        print("🔍 Testing real server on port 8001...")

        try:
            # Test with direct client creation
            async with EmbeddingServiceAsyncClient("http://localhost", 8001) as client:
                print(f"✅ Client: {client.base_url}:{client.port}")
                print(f"✅ SSL enabled: {client.is_ssl_enabled()}")
                print(f"✅ Authenticated: {client.is_authenticated()}")

                # Test health check
                health = await client.health()
                print(f"✅ Health: {health}")

                # Test help command without parameters
                help_result = await client.cmd("help")
                print(f"✅ Help: {len(help_result)} keys in response")

                # Test help command with parameters
                try:
                    help_with_params = await client.cmd("help", params={"command": "embed"})
                    print(f"✅ Help with params: {len(help_with_params)} keys in response")
                except Exception as e:
                    print(f"⚠️ Help with params: {e}")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts}
                embed_result = await client.cmd("embed", params=params)
                print(f"✅ Embed: {len(embed_result)} keys in response")

                return True

        except Exception as e:
            print(f"❌ Real server test failed: {e}")
            return False

    async def test_client_factory(self):
        """Test client factory methods."""
        print("🔍 Testing client factory methods...")

        try:
            # Test HTTP client factory
            http_client = ClientFactory.create_http_client("http://localhost", 10001)
            print(f"✅ HTTP factory client: {http_client.base_url}:{http_client.port}")
            await http_client.close()

            # Test HTTP token client factory
            http_token_client = ClientFactory.create_http_token_client(
                "http://localhost", 10002, "api_key", api_key="admin-secret-key"
            )
            print(f"✅ HTTP token factory client: {http_token_client.get_auth_method()}")
            await http_token_client.close()

            # Test HTTPS client factory
            https_client = ClientFactory.create_https_client("https://localhost", 10011)
            print(f"✅ HTTPS factory client: {https_client.base_url}:{https_client.port}")
            await https_client.close()

            return True

        except Exception as e:
            print(f"❌ Client factory test failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all client tests."""
        print("🧪 Starting comprehensive client tests...")
        print("=" * 60)

        # Test all security modes
        tests = [
            ("http_plain", self.test_http_plain),
            ("http_token", self.test_http_token),
            ("https_plain", self.test_https_plain),
            ("https_token", self.test_https_token),
            ("mtls_plain", self.test_mtls_plain),
            ("mtls_roles", self.test_mtls_roles),
            ("real_server_8001", self.test_real_server_8001),
            ("client_factory", self.test_client_factory),
        ]

        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name} test...")
            success = await test_func()
            self.test_results[test_name] = success

        # Print results
        print("\n📊 Test Results:")
        print("=" * 50)
        for test_name, success in self.test_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name:20} {status}")

        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for success in self.test_results.values() if success)
        failed_tests = total_tests - passed_tests

        print(f"\n🎉 Testing completed!")
        print(f"📊 Results: {passed_tests}/{total_tests} tests passed")
        if failed_tests > 0:
            print(f"❌ {failed_tests} tests failed")
        else:
            print("✅ All tests passed!")


async def main():
    """Main entry point."""
    tester = ClientExamplesTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
