#!/usr/bin/env python3
"""
Demo CLI Application for Text Vectorization
Simple demonstration of the CLI functionality.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from embed_client.cli import VectorizationCLI


async def demo_vectorization():
    """Demonstrate vectorization functionality."""
    print("🚀 Embed-Client CLI Demo")
    print("=" * 40)

    # Configuration for demo
    config = {
        "server": {"host": "http://localhost", "port": 8001},
        "auth": {"method": "none"},
        "ssl": {"enabled": False},
        "security": {"enabled": False},
    }

    cli = VectorizationCLI()

    try:
        # Connect to service
        print("🔌 Connecting to embedding service...")
        if not await cli.connect(config):
            print("❌ Failed to connect to service")
            return

        # Health check
        print("\n🏥 Checking service health...")
        await cli.health_check()

        # Get help
        print("\n❓ Getting help from service...")
        await cli.get_help()

        # Get commands
        print("\n📋 Getting available commands...")
        await cli.get_commands()

        # Vectorize texts
        print("\n🔤 Vectorizing texts...")
        texts = ["Hello world", "This is a test", "Machine learning is awesome"]

        print(f"📝 Vectorizing {len(texts)} texts:")
        for i, text in enumerate(texts):
            print(f"  {i+1}. {text}")

        await cli.vectorize_texts(texts, "json")

        print("\n✅ Demo completed successfully!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        await cli.disconnect()


async def main():
    """Main demo function."""
    await demo_vectorization()


if __name__ == "__main__":
    asyncio.run(main())
