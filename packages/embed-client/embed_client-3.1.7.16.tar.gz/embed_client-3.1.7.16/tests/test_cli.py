#!/usr/bin/env python3
"""
Test CLI Application
Tests the CLI functionality for text vectorization.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from embed_client.cli import VectorizationCLI


class CLITester:
    """Tester for CLI functionality."""

    def __init__(self):
        self.test_results = {}

    async def test_cli_connection(self):
        """Test CLI connection."""
        print("🔍 Testing CLI connection...")

        config = {
            "server": {"host": "http://localhost", "port": 8001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
            "security": {"enabled": False},
        }

        cli = VectorizationCLI()

        try:
            # Test connection
            if not await cli.connect(config):
                return False

            # Test health check
            health_ok = await cli.health_check()
            if not health_ok:
                return False

            # Test help
            await cli.get_help()

            # Test commands
            await cli.get_commands()

            # Test vectorization
            texts = ["hello world", "test text"]
            embeddings = await cli.vectorize_texts(texts, "json")

            if embeddings and len(embeddings) == len(texts):
                print("✅ CLI connection test passed")
                return True
            else:
                print("❌ CLI vectorization failed")
                return False

        except Exception as e:
            print(f"❌ CLI connection test failed: {e}")
            return False
        finally:
            await cli.disconnect()

    async def test_cli_with_auth(self):
        """Test CLI with authentication."""
        print("🔍 Testing CLI with authentication...")

        config = {
            "server": {"host": "http://localhost", "port": 10002},
            "auth": {"method": "api_key"},
            "ssl": {"enabled": False},
            "security": {"enabled": True, "tokens": {"user": "admin-secret-key"}},
        }

        cli = VectorizationCLI()

        try:
            # Test connection with auth
            if not await cli.connect(config):
                return False

            # Test health check
            health_ok = await cli.health_check()
            if not health_ok:
                return False

            # Test vectorization
            texts = ["authenticated text"]
            embeddings = await cli.vectorize_texts(texts, "json")

            if embeddings and len(embeddings) == len(texts):
                print("✅ CLI auth test passed")
                return True
            else:
                print("❌ CLI auth vectorization failed")
                return False

        except Exception as e:
            print(f"❌ CLI auth test failed: {e}")
            return False
        finally:
            await cli.disconnect()

    async def test_cli_with_ssl(self):
        """Test CLI with SSL."""
        print("🔍 Testing CLI with SSL...")

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

        cli = VectorizationCLI()

        try:
            # Test connection with SSL
            if not await cli.connect(config):
                return False

            # Test health check
            health_ok = await cli.health_check()
            if not health_ok:
                return False

            # Test vectorization
            texts = ["ssl text"]
            embeddings = await cli.vectorize_texts(texts, "json")

            if embeddings and len(embeddings) == len(texts):
                print("✅ CLI SSL test passed")
                return True
            else:
                print("❌ CLI SSL vectorization failed")
                return False

        except Exception as e:
            print(f"❌ CLI SSL test failed: {e}")
            return False
        finally:
            await cli.disconnect()

    async def test_cli_output_formats(self):
        """Test CLI output formats."""
        print("🔍 Testing CLI output formats...")

        config = {
            "server": {"host": "http://localhost", "port": 8001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False},
            "security": {"enabled": False},
        }

        cli = VectorizationCLI()

        try:
            if not await cli.connect(config):
                return False

            texts = ["format test"]

            # Test JSON format
            print("Testing JSON format...")
            embeddings_json = await cli.vectorize_texts(texts, "json")

            # Test CSV format
            print("Testing CSV format...")
            embeddings_csv = await cli.vectorize_texts(texts, "csv")

            # Test vectors format
            print("Testing vectors format...")
            embeddings_vectors = await cli.vectorize_texts(texts, "vectors")

            if all([embeddings_json, embeddings_csv, embeddings_vectors]):
                print("✅ CLI output formats test passed")
                return True
            else:
                print("❌ CLI output formats test failed")
                return False

        except Exception as e:
            print(f"❌ CLI output formats test failed: {e}")
            return False
        finally:
            await cli.disconnect()

    async def run_all_tests(self):
        """Run all CLI tests."""
        print("🧪 Starting CLI tests...")
        print("=" * 40)

        tests = [
            ("cli_connection", self.test_cli_connection),
            ("cli_auth", self.test_cli_with_auth),
            ("cli_ssl", self.test_cli_with_ssl),
            ("cli_formats", self.test_cli_output_formats),
        ]

        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name} test...")
            success = await test_func()
            self.test_results[test_name] = success

        # Print results
        print("\n📊 CLI Test Results:")
        print("=" * 30)
        for test_name, success in self.test_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name:15} {status}")

        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for success in self.test_results.values() if success)
        failed_tests = total_tests - passed_tests

        print(f"\n🎉 CLI Testing completed!")
        print(f"📊 Results: {passed_tests}/{total_tests} tests passed")
        if failed_tests > 0:
            print(f"❌ {failed_tests} tests failed")
        else:
            print("✅ All CLI tests passed!")


async def main():
    """Main test function."""
    tester = CLITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
