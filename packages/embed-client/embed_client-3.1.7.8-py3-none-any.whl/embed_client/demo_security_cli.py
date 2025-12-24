#!/usr/bin/env python3
"""
Demo Security CLI Application
Demonstrates all 8 security modes using the security CLI.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from embed_client.security_cli import SecurityCLI, create_config_from_security_mode


async def demo_security_mode(mode: str, host: str, port: int, **kwargs):
    """Demonstrate a specific security mode."""
    print(f"\n🔐 Demonstrating {mode} mode...")
    print("=" * 50)

    # Create configuration
    config = create_config_from_security_mode(mode, host, port, **kwargs)

    cli = SecurityCLI()

    try:
        # Connect to service
        print(f"🔌 Connecting using {mode} mode...")
        if not await cli.connect(config):
            print(f"❌ Failed to connect using {mode} mode")
            return False

        # Health check
        print(f"🏥 Checking service health...")
        health_ok = await cli.health_check()
        if not health_ok:
            print(f"❌ Health check failed for {mode} mode")
            return False

        # Get help
        print(f"❓ Getting help from service...")
        await cli.get_help()

        # Get commands
        print(f"📋 Getting available commands...")
        await cli.get_commands()

        # Vectorize texts
        texts = [
            f"Hello from {mode} mode",
            f"Security test for {mode}",
            f"Vectorization using {mode}",
        ]

        print(f"🔤 Vectorizing {len(texts)} texts using {mode} mode...")
        for i, text in enumerate(texts):
            print(f"  {i+1}. {text}")

        # Test different output formats
        print(f"\n📊 Testing JSON format:")
        await cli.vectorize_texts(texts, "json")

        print(f"\n📊 Testing CSV format:")
        await cli.vectorize_texts(texts, "csv")

        print(f"\n📊 Testing vectors format:")
        await cli.vectorize_texts(texts, "vectors")

        print(f"✅ {mode} mode demonstration completed successfully!")
        return True

    except Exception as e:
        print(f"❌ {mode} mode demonstration failed: {e}")
        return False
    finally:
        await cli.disconnect()


async def demo_all_security_modes():
    """Demonstrate all 8 security modes."""
    print("🚀 Security CLI Demo - All 8 Security Modes")
    print("=" * 60)

    # Demo configurations for each mode
    demos = [
        {
            "mode": "http",
            "host": "localhost",
            "port": 10001,
            "description": "Plain HTTP without authentication",
        },
        {
            "mode": "http_token",
            "host": "localhost",
            "port": 10002,
            "api_key": "admin-secret-key",
            "description": "HTTP with API Key authentication",
        },
        {
            "mode": "http_token_roles",
            "host": "localhost",
            "port": 10003,
            "api_key": "admin-secret-key",
            "description": "HTTP with API Key and role-based access control",
        },
        {
            "mode": "https",
            "host": "localhost",
            "port": 10011,
            "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
            "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
            "description": "HTTPS with server certificate verification",
        },
        {
            "mode": "https_token",
            "host": "localhost",
            "port": 10012,
            "api_key": "admin-secret-key",
            "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
            "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
            "description": "HTTPS with server certificates + authentication",
        },
        {
            "mode": "https_token_roles",
            "host": "localhost",
            "port": 10013,
            "api_key": "admin-secret-key",
            "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
            "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key",
            "description": "HTTPS with server certificates + authentication + roles",
        },
        {
            "mode": "mtls",
            "host": "localhost",
            "port": 10021,
            "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/client/embedding-service.crt",
            "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/client/embedding-service.key",
            "ca_cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/ca/ca.crt",
            "description": "Mutual TLS with client and server certificates",
        },
        {
            "mode": "mtls_roles",
            "host": "localhost",
            "port": 10022,
            "cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/client/embedding-service.crt",
            "key_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/client/embedding-service.key",
            "ca_cert_file": "/home/vasilyvz/projects/embed-client/mtls_certificates/ca/ca.crt",
            "description": "mTLS with role-based access control",
        },
    ]

    results = {}

    for demo in demos:
        mode = demo["mode"]
        description = demo["description"]

        print(f"\n🔐 {mode.upper()} - {description}")
        print("-" * 50)

        # Extract parameters for the demo
        demo_params = {
            k: v
            for k, v in demo.items()
            if k not in ["mode", "host", "port", "description"]
        }

        success = await demo_security_mode(
            demo["mode"], demo["host"], demo["port"], **demo_params
        )

        results[mode] = success

    # Print summary
    print("\n📊 Demo Results Summary:")
    print("=" * 50)
    for mode, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{mode:20} {status}")

    total_demos = len(results)
    successful_demos = sum(1 for success in results.values() if success)
    failed_demos = total_demos - successful_demos

    print(f"\n🎉 Demo completed!")
    print(f"📊 Results: {successful_demos}/{total_demos} demos successful")
    if failed_demos > 0:
        print(f"❌ {failed_demos} demos failed")
    else:
        print("✅ All demos successful!")


async def main():
    """Main demo function."""
    await demo_all_security_modes()


if __name__ == "__main__":
    asyncio.run(main())
