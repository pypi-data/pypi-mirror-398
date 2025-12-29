"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Configuration loader with priority support.

Priority order:
1. CLI/API arguments (highest)
2. Environment variables
3. Configuration file (lowest)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from svo_client.client_config_generator import ClientConfigGenerator
from svo_client.config_utils import generate_config


class ConfigLoader:
    """Load configuration with priority: CLI/API > env vars > config file."""

    @staticmethod
    def load_from_env() -> Dict[str, Any]:
        """Load configuration from environment variables.

        Returns:
            Configuration dictionary from environment variables.
        """
        host = os.getenv("SVO_HOST", "localhost")
        port_str = os.getenv("SVO_PORT", "8009")
        try:
            port = int(port_str)
        except ValueError:
            port = 8009

        cert = os.getenv("SVO_CERT")
        key = os.getenv("SVO_KEY")
        ca = os.getenv("SVO_CA")
        token = os.getenv("SVO_TOKEN")
        token_header = os.getenv(
            "SVO_TOKEN_HEADER", "X-API-Key"
        )

        timeout_str = os.getenv("SVO_TIMEOUT")
        timeout = float(timeout_str) if timeout_str else None

        config = generate_config(
            host=host,
            port=port,
            cert=cert,
            key=key,
            ca=ca,
            token=token,
            token_header=token_header,
        )
        if timeout is not None:
            config["timeout"] = timeout
        return config

    @staticmethod
    def load_from_file(
        config_path: Optional[str | Path] = None,
    ) -> Optional[Dict[str, Any]]:
        """Load configuration from file.

        Args:
            config_path: Path to config file. If None, tries SVO_CONFIG env var
                or default "client_config.json".

        Returns:
            Configuration dictionary or None if file not found.
        """
        if config_path is None:
            config_path = os.getenv("SVO_CONFIG", "client_config.json")

        path = Path(config_path)
        if not path.exists():
            return None

        try:
            return ClientConfigGenerator.load_config(path)
        except Exception:
            return None

    @staticmethod
    def merge_configs(
        *configs: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Merge multiple configurations with priority.

        Later configs override earlier ones (higher priority).

        Args:
            *configs: Configuration dictionaries in priority order
                (lowest to highest).

        Returns:
            Merged configuration dictionary.
        """
        merged: Dict[str, Any] = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        for config in configs:
            if not config:
                continue

            # Merge server section
            if "server" in config:
                server = config["server"]
                if isinstance(server, dict):
                    merged["server"].update(server)

            # Merge SSL section
            if "ssl" in config:
                ssl = config["ssl"]
                if isinstance(ssl, dict):
                    merged["ssl"].update(ssl)

            # Merge auth section
            if "auth" in config:
                auth = config["auth"]
                if isinstance(auth, dict):
                    merged["auth"].update(auth)

        return merged

    @staticmethod
    def resolve_config(
        *,
        config: Optional[Dict[str, Any]] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        cert: Optional[str] = None,
        key: Optional[str] = None,
        ca: Optional[str] = None,
        token: Optional[str] = None,
        token_header: Optional[str] = None,
        check_hostname: Optional[bool] = None,
        config_file: Optional[str | Path] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Resolve configuration with priority:
        CLI/API > env vars > config file.

        Args:
            config: Pre-built config dict (highest priority if provided).
            host: Server hostname (CLI/API priority).
            port: Server port (CLI/API priority).
            cert: Client certificate path (CLI/API priority).
            key: Client key path (CLI/API priority).
            ca: CA certificate path (CLI/API priority).
            token: API token (CLI/API priority).
            token_header: Token header name (CLI/API priority).
            check_hostname: Check hostname flag (CLI/API priority).
            config_file: Path to config file (overrides SVO_CONFIG env var).

        Returns:
            Resolved configuration dictionary.
        """
        # Priority 3: Config file (lowest)
        file_config = ConfigLoader.load_from_file(config_file)

        # Priority 2: Environment variables
        env_config = ConfigLoader.load_from_env()

        # Priority 1: CLI/API arguments (highest)
        api_config: Optional[Dict[str, Any]] = None
        if (
            host is not None
            or port is not None
            or cert is not None
            or key is not None
            or ca is not None
            or token is not None
            or token_header is not None
            or check_hostname is not None
        ):
            # Build config from API parameters
            server_section = env_config.get("server", {})
            ssl_section = env_config.get("ssl", {})
            auth_section = env_config.get("auth", {})

            default_host = server_section.get("host", "localhost")
            default_port = server_section.get("port", 8009)
            api_host = host or default_host
            api_port = port or default_port
            api_cert = cert or ssl_section.get("cert_file")
            api_key = key or ssl_section.get("key_file")
            api_ca = ca or ssl_section.get(
                "ca_cert_file"
            )
            api_keys = auth_section.get("api_keys", {})
            api_token = token or api_keys.get("default")
            default_header = auth_section.get("header", "X-API-Key")
            api_token_header = token_header or default_header

            api_config = generate_config(
                host=api_host,
                port=api_port,
                cert=api_cert,
                key=api_key,
                ca=api_ca,
                token=api_token,
                token_header=api_token_header,
            )

            # Override check_hostname if provided
            if check_hostname is not None:
                ssl_section = api_config.setdefault("ssl", {})
                ssl_section["check_hostname"] = check_hostname

            # Add timeout if provided via API
            if timeout is not None:
                api_config["timeout"] = timeout
            else:
                # Get timeout from env config if not provided via API
                config_timeout = env_config.get("timeout")
                if config_timeout is not None:
                    # Try file config
                    config_timeout = (
                        file_config.get("timeout") if file_config else None
                    )
                if config_timeout is not None:
                    api_config["timeout"] = config_timeout

        # Merge with priority: file < env < api
        if config:
            # Pre-built config has highest priority
            return config

        merged = ConfigLoader.merge_configs(
            file_config, env_config, api_config
        )
        return merged
