#!python
"""
CLI tool to generate client configuration files.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Usage:
    # Interactive mode
    python generate_client_config.py

    # From environment variables
    SVO_HOST=localhost SVO_PORT=8009 python generate_client_config.py --env

    # From command line arguments
    python generate_client_config.py --host localhost --port 8009 \\
        --cert cert.crt --key key.key --ca ca.crt
"""

import argparse
import sys

from svo_client.client_config_generator import ClientConfigGenerator


def main() -> int:
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Generate client configuration file for ChunkerClient"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="client_config.json",
        help="Output config file name (default: client_config.json)",
    )
    parser.add_argument(
        "--output-dir",
        "-d",
        type=str,
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "--env",
        action="store_true",
        help="Generate from environment variables",
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Server hostname",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Server port",
    )
    parser.add_argument(
        "--cert",
        type=str,
        help="Client certificate file path",
    )
    parser.add_argument(
        "--key",
        type=str,
        help="Client private key file path",
    )
    parser.add_argument(
        "--ca",
        type=str,
        help="CA certificate file path",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="API token",
    )
    parser.add_argument(
        "--token-header",
        type=str,
        default="X-API-Key",
        help="Token header name (default: X-API-Key)",
    )
    parser.add_argument(
        "--roles",
        type=str,
        help="Comma-separated list of roles",
    )
    parser.add_argument(
        "--check-hostname",
        action="store_true",
        help="Check hostname in SSL certificate",
    )

    args = parser.parse_args()

    try:
        # Determine generation mode
        if args.env:
            # From environment variables
            output_path = ClientConfigGenerator.generate_from_env(
                config_name=args.output,
                output_dir=args.output_dir,
            )
        elif args.host or args.port or args.cert or args.token:
            # From command line arguments
            roles = None
            if args.roles:
                roles = [r.strip() for r in args.roles.split(",") if r.strip()]

            output_path = ClientConfigGenerator.generate_from_params(
                host=args.host or "localhost",
                port=args.port or 8009,
                cert=args.cert,
                key=args.key,
                ca=args.ca,
                token=args.token,
                token_header=args.token_header,
                roles=roles,
                check_hostname=args.check_hostname,
                config_name=args.output,
                output_dir=args.output_dir,
            )
        else:
            # Interactive mode
            output_path = ClientConfigGenerator.generate_interactive(
                config_name=args.output,
                output_dir=args.output_dir,
            )

        print(f"\n✅ Client configuration generated: {output_path}")
        return 0

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
