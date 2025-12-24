#!/usr/bin/env python3
"""
Test Security CLI Application.

Runs all security-mode checks via helper coroutines.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
from typing import Any, Dict, List, Tuple

from security_cli_tests_modes import (
    test_http_mode,
    test_http_token_mode,
    test_http_token_roles_mode,
    test_https_mode,
    test_https_token_mode,
    test_https_token_roles_mode,
    test_mtls_mode,
    test_mtls_roles_mode,
    test_output_formats,
)


async def main() -> None:
    """Entry point for manual security CLI testing."""
    tests: List[Tuple[str, Any]] = [
        ("http", test_http_mode),
        ("http_token", test_http_token_mode),
        ("http_token_roles", test_http_token_roles_mode),
        ("https", test_https_mode),
        ("https_token", test_https_token_mode),
        ("https_token_roles", test_https_token_roles_mode),
        ("mtls", test_mtls_mode),
        ("mtls_roles", test_mtls_roles_mode),
        ("output_formats", test_output_formats),
    ]

    results: Dict[str, bool] = {}

    print("🧪 Starting comprehensive security mode tests...")
    print("=" * 60)

    for name, func in tests:
        print(f"\n🔍 Running {name} test...")
        success = await func()
        results[name] = bool(success)

    print("\n📊 Security Mode Test Results:")
    print("=" * 50)
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:20} {status}")

    total = len(results)
    passed = sum(1 for success in results.values() if success)
    failed = total - passed

    print("\n🎉 Security testing completed!")
    print(f"📊 Results: {passed}/{total} tests passed")
    if failed > 0:
        print(f"❌ {failed} tests failed")
    else:
        print("✅ All security mode tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
