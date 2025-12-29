#!/usr/bin/env python3
"""
CLI tool to validate client configuration files.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Usage:
    # Validate a config file
    python validate_client_config.py client_config.json

    # Validate and show details
    python validate_client_config.py client_config.json --verbose

    # Validate from stdin
    cat client_config.json | python validate_client_config.py -
"""

import argparse
import json
import sys
from pathlib import Path

from svo_client.client_config_generator import ClientConfigGenerator
from svo_client.config_tools import ConfigValidator


def validate_file(
    config_path: str | Path, verbose: bool = False
) -> tuple[bool, list[str]]:
    """Validate a configuration file.

    Args:
        config_path: Path to configuration file or "-" for stdin.
        verbose: Show detailed validation information.

    Returns:
        Tuple of (is_valid, error_messages).
    """
    errors: list[str] = []

    try:
        # Load config
        if config_path == "-" or str(config_path) == "-":
            config = json.load(sys.stdin)
            source = "stdin"
        else:
            config = ClientConfigGenerator.load_config(config_path)
            source = str(config_path)

        if verbose:
            print(f"📝 Validating configuration from: {source}")

        # Validate structure
        try:
            validated = ConfigValidator.validate(config)
            if verbose:
                print("✅ Configuration structure is valid")

            # Additional checks
            server = validated.get("server", {})
            ssl = validated.get("ssl", {})
            auth = validated.get("auth", {})

            if verbose:
                print("\n📊 Configuration details:")
                host = server.get("host", "N/A")
                port = server.get("port", "N/A")
                print(f"   Server: {host}:{port}")
                ssl_status = "enabled" if ssl.get("enabled") else "disabled"
                print(f"   SSL: {ssl_status}")
                if ssl.get("enabled"):
                    verify_mode = ssl.get("verify_mode", "NONE")
                    print(f"   SSL verify_mode: {verify_mode}")
                if verify_mode == "CERT_REQUIRED":
                    cert_file = ssl.get("cert_file", "N/A")
                    key_file = ssl.get("key_file", "N/A")
                    ca_file = ssl.get("ca_cert_file", "N/A")
                    print(f"   Certificate: {cert_file}")
                    print(f"   Key: {key_file}")
                    print(f"   CA: {ca_file}")
                print(f"   Auth: {auth.get('method', 'none')}")
                if auth.get("method") == "api_key":
                    print(f"   Token header: {auth.get('header', 'N/A')}")

            # Check file paths if SSL is enabled
            ssl_enabled = ssl.get("enabled")
            verify_mode = ssl.get("verify_mode")
            if ssl_enabled and verify_mode == "CERT_REQUIRED":
                cert_file = ssl.get("cert_file")
                key_file = ssl.get("key_file")
                ca_file = ssl.get("ca_cert_file")

                if cert_file and not Path(cert_file).exists():
                    errors.append(
                        f"Certificate file not found: {cert_file}"
                    )
                if key_file and not Path(key_file).exists():
                    errors.append(
                        f"Key file not found: {key_file}"
                    )
                if ca_file and not Path(ca_file).exists():
                    errors.append(f"CA file not found: {ca_file}")

            if errors:
                if verbose:
                    print("\n⚠️  Validation warnings:")
                    for error in errors:
                        print(f"   - {error}")
                return False, errors

            if verbose:
                print("\n✅ Configuration is valid and ready to use")
            return True, []

        except ValueError as e:
            errors.append(str(e))
            return False, errors

    except FileNotFoundError as e:
        errors.append(f"Config file not found: {e}")
        return False, errors
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Validation error: {e}")
        return False, errors


def main() -> int:
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Validate client configuration file for ChunkerClient"
    )
    parser.add_argument(
        "config",
        type=str,
        help="Path to configuration file or '-' for stdin",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed validation information",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 0 if valid, 1 if invalid (for CI)",
    )

    args = parser.parse_args()

    is_valid, errors = validate_file(args.config, verbose=args.verbose)

    if is_valid:
        if not args.verbose:
            print("✅ Configuration is valid")
        return 0
    else:
        if not args.verbose:
            print("❌ Configuration is invalid:")
            for error in errors:
                print(f"   - {error}")
        return 1 if args.exit_code else 0


if __name__ == "__main__":
    sys.exit(main())
