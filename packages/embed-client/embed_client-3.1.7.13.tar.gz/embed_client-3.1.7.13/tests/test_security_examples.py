#!/usr/bin/env python3
"""
Test Security Examples
Tests all security modes using MCP Security Framework examples.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add the framework to the path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent / ".venv" / "lib" / "python3.12" / "site-packages"),
)

from embed_client.async_client import EmbeddingServiceAsyncClient


class SecurityExamplesTester:
    """Tester for all security examples."""

    def __init__(self):
        self.test_results = {}
        self.logger = logging.getLogger(__name__)

    async def test_http_simple(self):
        """Test HTTP simple mode."""
        print("🔍 Testing HTTP simple mode...")

        config = {
            "server": {"host": "http://localhost", "port": 10001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
            "security": {"enabled": False},
        }

        try:
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                # Test health
                result = await client.health()
                assert "status" in result
                print(f"✅ HTTP simple health: {result['status']}")

                # Test help
                result = await client.cmd("help")
                assert isinstance(result, dict)
                print(f"✅ HTTP simple help: OK")

                # Test embed
                texts = ["hello world", "test embedding"]
                # Use error_policy="continue" to align with production contract
                params = {"texts": texts, "error_policy": "continue"}
                result = await client.cmd("embed", params=params)
                assert isinstance(result, dict)
                print(f"✅ HTTP simple embed: OK")

                return True

        except Exception as e:
            print(f"❌ HTTP simple test failed: {e}")
            return False

    async def test_http_token(self):
        """Test HTTP with token mode."""
        print("🔍 Testing HTTP token mode...")

        config = {
            "server": {"host": "http://localhost", "port": 10002},
            "auth": {"method": "api_key"},
            "ssl": {"enabled": False},
            "security": {
                "enabled": True,
                "tokens": {
                    "admin": "admin-secret-key",
                    "user": "user-secret-key",
                    "readonly": "readonly-secret-key",
                },
            },
        }

        try:
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                # Test health
                result = await client.health()
                assert "status" in result
                print(f"✅ HTTP token health: {result['status']}")

                # Test help
                result = await client.cmd("help")
                assert isinstance(result, dict)
                print(f"✅ HTTP token help: OK")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts, "error_policy": "continue"}
                result = await client.cmd("embed", params=params)
                assert isinstance(result, dict)
                print(f"✅ HTTP token embed: OK")

                return True

        except Exception as e:
            print(f"❌ HTTP token test failed: {e}")
            return False

    async def test_https_simple(self):
        """Test HTTPS simple mode."""
        print("🔍 Testing HTTPS simple mode...")

        config = {
            "server": {"host": "https://localhost", "port": 10011},
            "auth": {"method": "none"},
            "ssl": {
                "enabled": True,
                "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
                "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
            },
            "security": {"enabled": False},
        }

        try:
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                # Test health
                result = await client.health()
                assert "status" in result
                print(f"✅ HTTPS simple health: {result['status']}")

                # Test help
                result = await client.cmd("help")
                assert isinstance(result, dict)
                print(f"✅ HTTPS simple help: OK")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts, "error_policy": "continue"}
                result = await client.cmd("embed", params=params)
                assert isinstance(result, dict)
                print(f"✅ HTTPS simple embed: OK")

                return True

        except Exception as e:
            print(f"❌ HTTPS simple test failed: {e}")
            return False

    async def test_https_token(self):
        """Test HTTPS with token mode."""
        print("🔍 Testing HTTPS token mode...")

        config = {
            "server": {"host": "https://localhost", "port": 10012},
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
            },
        }

        try:
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                # Test health
                result = await client.health()
                assert "status" in result
                print(f"✅ HTTPS token health: {result['status']}")

                # Test help
                result = await client.cmd("help")
                assert isinstance(result, dict)
                print(f"✅ HTTPS token help: OK")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts, "error_policy": "continue"}
                result = await client.cmd("embed", params=params)
                assert isinstance(result, dict)
                print(f"✅ HTTPS token embed: OK")

                return True

        except Exception as e:
            print(f"❌ HTTPS token test failed: {e}")
            return False

    async def test_mtls_simple(self):
        """Test mTLS simple mode."""
        print("🔍 Testing mTLS simple mode...")

        config = {
            "server": {"host": "https://localhost", "port": 10021},
            "auth": {"method": "certificate"},
            "ssl": {
                "enabled": True,
                "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
                "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
                "ca_cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/ca/ca.crt",
            },
            "security": {"enabled": False},
        }

        try:
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                # Test health
                result = await client.health()
                assert "status" in result
                print(f"✅ mTLS simple health: {result['status']}")

                # Test help
                result = await client.cmd("help")
                assert isinstance(result, dict)
                print(f"✅ mTLS simple help: OK")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts, "error_policy": "continue"}
                result = await client.cmd("embed", params=params)
                assert isinstance(result, dict)
                print(f"✅ mTLS simple embed: OK")

                return True

        except Exception as e:
            print(f"❌ mTLS simple test failed: {e}")
            return False

    async def test_mtls_roles(self):
        """Test mTLS with roles mode."""
        print("🔍 Testing mTLS roles mode...")

        config = {
            "server": {"host": "https://localhost", "port": 10022},
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
        }

        try:
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                # Test health
                result = await client.health()
                assert "status" in result
                print(f"✅ mTLS roles health: {result['status']}")

                # Test help
                result = await client.cmd("help")
                assert isinstance(result, dict)
                print(f"✅ mTLS roles help: OK")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts, "error_policy": "continue"}
                result = await client.cmd("embed", params=params)
                assert isinstance(result, dict)
                print(f"✅ mTLS roles embed: OK")

                return True

        except Exception as e:
            print(f"❌ mTLS roles test failed: {e}")
            return False

    async def test_real_server_8001(self):
        """Test real server on port 8001."""
        print("🔍 Testing real server on port 8001...")

        config = {
            "server": {"host": "http://localhost", "port": 8001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
            "security": {"enabled": False},
        }

        try:
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                # Test health
                result = await client.health()
                assert "status" in result
                print(f"✅ Real server health: {result['status']}")

                # Test help without parameters
                result = await client.cmd("help")
                assert isinstance(result, dict)
                print(f"✅ Real server help: OK")

                # Test help with parameters
                try:
                    result = await client.cmd("help", params={"command": "embed"})
                    assert isinstance(result, dict)
                    print(f"✅ Real server help with params: OK")
                except Exception as e:
                    print(f"⚠️ Real server help with params: {e}")

                # Test embed
                texts = ["hello world", "test embedding"]
                params = {"texts": texts}
                result = await client.cmd("embed", params=params)
                assert isinstance(result, dict)
                print(f"✅ Real server embed: OK")

                return True

        except Exception as e:
            print(f"❌ Real server test failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all security tests."""
        print("🧪 Starting comprehensive security tests...")
        print("=" * 60)

        # Test all security modes
        tests = [
            ("http_simple", self.test_http_simple),
            ("http_token", self.test_http_token),
            ("https_simple", self.test_https_simple),
            ("https_token", self.test_https_token),
            ("mtls_simple", self.test_mtls_simple),
            ("mtls_roles", self.test_mtls_roles),
            ("real_server_8001", self.test_real_server_8001),
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
    tester = SecurityExamplesTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
