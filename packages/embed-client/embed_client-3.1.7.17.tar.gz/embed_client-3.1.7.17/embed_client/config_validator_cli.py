"""
CLI entry point for the embed-client configuration validator.

This module provides the command-line interface for validating configuration
files using `ConfigValidator`.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from embed_client.config_validator import ConfigValidator


def main() -> int:
    """
    CLI entry point for the configuration validator.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Validate embed-client configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a single config file
  embed-config-validator --file configs/http.json

  # Validate all configs in a directory
  embed-config-validator --dir configs

  # Validate and show detailed errors
  embed-config-validator --file configs/mtls.json --verbose
        """,
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to configuration file to validate",
    )
    parser.add_argument(
        "--dir",
        type=str,
        help="Directory containing configuration files to validate",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed error messages",
    )

    args = parser.parse_args()

    if not args.file and not args.dir:
        parser.print_help()
        return 1

    validator = ConfigValidator()

    if args.file:
        # Validate single file
        config_path = Path(args.file)
        if not config_path.is_absolute():
            config_path = Path.cwd() / config_path

        print(f"🔍 Validating: {config_path}")
        is_valid, message, errors = validator.validate_config_file(config_path)

        if is_valid:
            print(f"✅ Configuration is valid: {message}")
            return 0
        else:
            print(f"❌ Configuration validation failed: {message}")
            if errors and args.verbose:
                print("\nErrors:")
                for error in errors:
                    print(f"  • {error}")
            elif errors:
                print(f"  Found {len(errors)} error(s). Use --verbose to see details.")
            return 1

    elif args.dir:
        # Validate directory
        config_dir = Path(args.dir)
        if not config_dir.is_absolute():
            config_dir = Path.cwd() / config_dir

        if not config_dir.exists():
            print(f"❌ Directory not found: {config_dir}")
            return 1

        print(f"🔍 Validating configurations in: {config_dir}")
        print("=" * 70)

        results = validator.validate_config_directory(config_dir)

        if not results:
            print("⚠️  No configuration files found")
            return 1

        all_valid = True
        for config_name, (is_valid, message, errors) in results.items():
            status = "✅" if is_valid else "❌"
            print(f"{status} {config_name:35s} - {message}")

            if not is_valid:
                all_valid = False
                if errors and args.verbose:
                    for error in errors:
                        print(f"      ⚠️  {error}")

        print("=" * 70)

        if all_valid:
            print(f"✅ All {len(results)} configuration files are valid!")
            return 0
        else:
            failed = [
                (name, errors)
                for name, (valid, _, errors) in results.items()
                if not valid
            ]
            print(f"❌ {len(failed)} configuration file(s) failed validation:")
            for name, errors in failed:
                print(f"   - {name}")
                if args.verbose and errors:
                    for error in errors:
                        print(f"     • {error}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

