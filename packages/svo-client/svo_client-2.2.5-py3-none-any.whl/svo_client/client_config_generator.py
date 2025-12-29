"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Client configuration file generator.

This module provides tools to generate and save client configuration
files for ChunkerClient.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from svo_client.config_tools import ConfigGenerator


class ClientConfigGenerator:
    """Generate and save client configuration files."""

    @staticmethod
    def generate_from_env(
        config_name: str = "client_config.json",
        output_dir: Optional[str | Path] = None,
    ) -> Path:
        """Generate client config from environment variables.

        Environment variables:
            SVO_HOST: Server hostname (default: localhost)
            SVO_PORT: Server port (default: 8009)
            SVO_CERT: Path to client certificate file
            SVO_KEY: Path to client private key file
            SVO_CA: Path to CA certificate file
            SVO_TOKEN: API token for authentication
            SVO_TOKEN_HEADER: Token header name (default: X-API-Key)
            SVO_CHECK_HOSTNAME: Check hostname in SSL (default: false)
            SVO_ROLES: Comma-separated list of roles

        Args:
            config_name: Name of the output config file.
            output_dir: Directory to save config file.
                If None, saves to current directory.

        Returns:
            Path to generated config file.
        """
        host = os.getenv("SVO_HOST", "localhost")
        port = int(os.getenv("SVO_PORT", "8009") or "8009")
        cert = os.getenv("SVO_CERT")
        key = os.getenv("SVO_KEY")
        ca = os.getenv("SVO_CA")
        token = os.getenv("SVO_TOKEN")
        token_header = os.getenv("SVO_TOKEN_HEADER", "X-API-Key")
        check_hostname = (
            os.getenv("SVO_CHECK_HOSTNAME", "false").lower() == "true"
        )
        roles_str = os.getenv("SVO_ROLES")
        roles = (
            [r.strip() for r in roles_str.split(",") if r.strip()]
            if roles_str
            else None
        )

        # Determine protocol and generate config
        if cert and key and ca:
            # mTLS
            config = ConfigGenerator.mtls(
                host, port, cert, key, ca, roles, check_hostname
            )
            # Add token if provided (mTLS + token)
            if token:
                config["auth"]["method"] = "api_key"
                config["auth"]["header"] = token_header
                config["auth"]["api_keys"] = {"default": token}
                if roles:
                    config["auth"]["roles"] = roles
        elif token:
            # HTTPS with token
            config = ConfigGenerator.https_token(
                host, port, token, token_header, roles, check_hostname
            )
        elif cert or key or ca:
            # HTTPS without auth
            config = ConfigGenerator.https(host, port, check_hostname)
        else:
            # HTTP
            if token:
                config = ConfigGenerator.http_token(
                    host, port, token, token_header, roles
                )
            else:
                config = ConfigGenerator.http(host, port)

        # Save config
        output_path = ClientConfigGenerator.save_config(
            config, config_name, output_dir
        )
        return output_path

    @staticmethod
    def generate_interactive(
        config_name: str = "client_config.json",
        output_dir: Optional[str | Path] = None,
    ) -> Path:
        """Generate client config interactively.

        Args:
            config_name: Name of the output config file.
            output_dir: Directory to save config file.
                If None, saves to current directory.

        Returns:
            Path to generated config file.
        """
        print("🔧 Client Configuration Generator")
        print("=" * 60)

        # Server connection
        host = input("Server host [localhost]: ").strip() or "localhost"
        port_str = input("Server port [8009]: ").strip() or "8009"
        try:
            port = int(port_str)
        except ValueError:
            print("⚠️  Invalid port, using default 8009")
            port = 8009

        # SSL/TLS
        use_ssl = input("Use SSL/TLS? [y/N]: ").strip().lower() == "y"
        cert = None
        key = None
        ca = None
        check_hostname = False

        if use_ssl:
            cert = input("Client certificate file path: ").strip() or None
            key = input("Client private key file path: ").strip() or None
            ca = input("CA certificate file path: ").strip() or None
            check_hostname_prompt = (
                "Check hostname in certificate? [y/N]: "
            )
            check_hostname_str = (
                input(check_hostname_prompt).strip().lower()
            )
            check_hostname = check_hostname_str == "y"

        # Authentication
        use_token_prompt = "Use token authentication? [y/N]: "
        use_token = input(use_token_prompt).strip().lower() == "y"
        token = None
        token_header = "X-API-Key"
        roles = None

        if use_token:
            token = input("API token: ").strip() or None
            token_header_prompt = f"Token header [{token_header}]: "
            token_header_input = (
                input(token_header_prompt).strip() or token_header
            )
            token_header = token_header_input
            roles_str = input("Roles (comma-separated, optional): ").strip()
            if roles_str:
                roles = [r.strip() for r in roles_str.split(",") if r.strip()]

        # Generate config
        if cert and key and ca:
            config = ConfigGenerator.mtls(
                host, port, cert, key, ca, roles, check_hostname
            )
        elif use_ssl:
            if use_token and token:
                config = ConfigGenerator.https_token(
                    host, port, token, token_header, roles, check_hostname
                )
            else:
                config = ConfigGenerator.https(host, port, check_hostname)
        else:
            if use_token and token:
                config = ConfigGenerator.http_token(
                    host, port, token, token_header, roles
                )
            else:
                config = ConfigGenerator.http(host, port)

        # Save config
        output_path = ClientConfigGenerator.save_config(
            config, config_name, output_dir
        )
        print(f"\n✅ Configuration saved to: {output_path}")
        return output_path

    @staticmethod
    def generate_from_params(
        host: str = "localhost",
        port: int = 8009,
        cert: Optional[str] = None,
        key: Optional[str] = None,
        ca: Optional[str] = None,
        token: Optional[str] = None,
        token_header: str = "X-API-Key",
        roles: Optional[list[str]] = None,
        check_hostname: bool = False,
        config_name: str = "client_config.json",
        output_dir: Optional[str | Path] = None,
    ) -> Path:
        """Generate client config from parameters.

        Args:
            host: Server hostname.
            port: Server port.
            cert: Path to client certificate file.
            key: Path to client private key file.
            ca: Path to CA certificate file.
            token: API token for authentication.
            token_header: Token header name.
            roles: List of roles.
            check_hostname: Check hostname in SSL certificate.
            config_name: Name of the output config file.
            output_dir: Directory to save config file.

        Returns:
            Path to generated config file.
        """
        # Determine protocol and generate config
        if cert and key and ca:
            # mTLS
            config = ConfigGenerator.mtls(
                host, port, cert, key, ca, roles, check_hostname
            )
            # Add token if provided (mTLS + token)
            if token:
                config["auth"]["method"] = "api_key"
                config["auth"]["header"] = token_header
                config["auth"]["api_keys"] = {"default": token}
                if roles:
                    config["auth"]["roles"] = roles
        elif token:
            if cert or key or ca:
                config = ConfigGenerator.https_token(
                    host, port, token, token_header, roles, check_hostname
                )
            else:
                config = ConfigGenerator.http_token(
                    host, port, token, token_header, roles
                )
        elif cert or key or ca:
            config = ConfigGenerator.https(host, port, check_hostname)
        else:
            config = ConfigGenerator.http(host, port)

        return ClientConfigGenerator.save_config(
            config, config_name, output_dir
        )

    @staticmethod
    def save_config(
        config: Dict[str, Any],
        config_name: str = "client_config.json",
        output_dir: Optional[str | Path] = None,
    ) -> Path:
        """Save configuration to JSON file.

        Args:
            config: Configuration dictionary.
            config_name: Name of the output config file.
            output_dir: Directory to save config file.
                If None, saves to current directory.

        Returns:
            Path to saved config file.
        """
        if output_dir:
            output_path = Path(output_dir) / config_name
        else:
            output_path = Path(config_name)

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save config
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return output_path

    @staticmethod
    def load_config(config_path: str | Path) -> Dict[str, Any]:
        """Load client configuration from JSON file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If config file is invalid JSON.
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
