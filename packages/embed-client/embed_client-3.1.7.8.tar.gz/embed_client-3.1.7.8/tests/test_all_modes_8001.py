#!/usr/bin/env python3
"""
Comprehensive Test Pipeline for All Security Modes on localhost:8001
Tests vectorization (embedding) for all 8 security modes on real server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from embed_client.async_client import EmbeddingServiceAsyncClient, EmbeddingServiceError
from embed_client.config_generator import ClientConfigGenerator


class AllModes8001Tester:
    """Comprehensive tester for all 8 security modes on localhost:8001."""

    def __init__(self):
        self.test_results: Dict[str, bool] = {}
        self.test_texts = ["hello world", "test embedding", "vectorization test"]
        self.base_port = 8001
        self.mtls_certs_dir = Path(__file__).parent.parent / "mtls_certificates"
        self.config_generator = ClientConfigGenerator()

    def create_configs(self) -> Dict[str, Dict[str, Any]]:
        """Create configurations for all 8 security modes using generator."""
        cert_file = str(self.mtls_certs_dir / "client" / "embedding-service.crt")
        key_file = str(self.mtls_certs_dir / "client" / "embedding-service.key")
        ca_cert_file = str(self.mtls_certs_dir / "ca" / "ca.crt")

        # Generate all configurations using the generator
        configs = self.config_generator.generate_all_configs(
            host="localhost",
            port=self.base_port,
            output_dir=None,  # Don't save to disk, just return configs
            cert_file=cert_file if Path(cert_file).exists() else None,
            key_file=key_file if Path(key_file).exists() else None,
            ca_cert_file=ca_cert_file if Path(ca_cert_file).exists() else None,
        )

        return configs

    async def test_mode(self, mode_name: str, config: Dict[str, Any]) -> bool:
        """Test a specific security mode with vectorization."""
        print(f"\n🔍 Testing {mode_name} mode...")
        print(f"   Config: {json.dumps(config, indent=2)}")

        try:
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                # Test health check
                print(f"   ⏳ Health check...")
                try:
                    health_result = await client.health()
                    print(f"   ✅ Health: {health_result}")
                except Exception as e:
                    print(f"   ⚠️  Health check failed (may be expected): {e}")

                # Test vectorization (embedding)
                print(f"   ⏳ Vectorization test with {len(self.test_texts)} texts...")
                try:
                    result = await client.cmd("embed", params={"texts": self.test_texts})
                    print(f"   ✅ Vectorization successful!")

                    # Validate result
                    if isinstance(result, dict):
                        if "result" in result:
                            result_data = result["result"]
                            if isinstance(result_data, dict):
                                if "data" in result_data:
                                    data = result_data["data"]
                                    if "embeddings" in data or "results" in data:
                                        embeddings = data.get("embeddings") or [
                                            r.get("embedding") for r in data.get("results", [])
                                        ]
                                        if embeddings and len(embeddings) == len(self.test_texts):
                                            print(
                                                f"   ✅ Got {len(embeddings)} embeddings, "
                                                f"first embedding dimension: {len(embeddings[0]) if embeddings[0] else 0}"
                                            )
                                            return True
                                        else:
                                            print(
                                                f"   ❌ Wrong number of embeddings: "
                                                f"expected {len(self.test_texts)}, got {len(embeddings) if embeddings else 0}"
                                            )
                                            return False
                                    else:
                                        print(f"   ❌ No embeddings or results in data: {data.keys()}")
                                        return False
                                else:
                                    print(f"   ❌ No data in result: {result_data.keys()}")
                                    return False
                            else:
                                print(f"   ❌ Result is not a dict: {type(result_data)}")
                                return False
                        else:
                            print(f"   ❌ No result in response: {result.keys()}")
                            return False
                    else:
                        print(f"   ❌ Response is not a dict: {type(result)}")
                        return False

                except EmbeddingServiceError as e:
                    print(f"   ❌ Vectorization failed: {e}")
                    return False
                except Exception as e:
                    print(f"   ❌ Unexpected error during vectorization: {e}")
                    import traceback

                    traceback.print_exc()
                    return False

        except Exception as e:
            print(f"   ❌ Failed to create client or connect: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def run_all_tests(self) -> bool:
        """Run tests for all security modes."""
        print("=" * 80)
        print("🧪 Comprehensive Test Pipeline for All Security Modes on localhost:8001")
        print("=" * 80)
        print(f"📝 Test texts: {self.test_texts}")
        print(f"🌐 Server: localhost:{self.base_port}")
        print("=" * 80)

        configs = self.create_configs()

        for mode_name, config in configs.items():
            success = await self.test_mode(mode_name, config)
            self.test_results[mode_name] = success

            # Small delay between tests
            await asyncio.sleep(1)

        # Print summary
        print("\n" + "=" * 80)
        print("📊 Test Results Summary")
        print("=" * 80)

        total = len(self.test_results)
        passed = sum(1 for success in self.test_results.values() if success)
        failed = total - passed

        for mode_name, success in self.test_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{mode_name:20} {status}")

        print("=" * 80)
        print(f"📈 Total: {total} | ✅ Passed: {passed} | ❌ Failed: {failed}")
        print("=" * 80)

        if failed == 0:
            print("\n🎉 All tests passed!")
            return True
        else:
            print(f"\n⚠️  {failed} test(s) failed")
            return False


async def main():
    """Main entry point."""
    tester = AllModes8001Tester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
