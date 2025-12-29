"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Server configuration-based client config generator.

This module generates client configurations based on server
configuration files. It analyzes server configs and creates
corresponding client configs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from svo_client.config_tools import ConfigGenerator


class ServerConfigGenerator:
    """Generate client configs from server configuration files."""

    @staticmethod
    def load_server_config(config_path: str | Path) -> Dict[str, Any]:
        """Load server configuration from JSON file.

        Args:
            config_path: Path to server configuration file.

        Returns:
            Server configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If config file is invalid JSON.
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Server config file not found: {config_path}"
            )

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _resolve_path(
        path: Optional[str], base_dir: Optional[Path] = None
    ) -> Optional[str]:
        """Resolve relative paths to absolute paths.

        Args:
            path: Path to resolve (can be relative or absolute).
            base_dir: Base directory for resolving relative paths.

        Returns:
            Resolved absolute path or None if path is None.
        """
        if not path:
            return None

        path_obj = Path(path)
        if path_obj.is_absolute():
            return str(path_obj)

        if base_dir:
            resolved = (base_dir / path).resolve()
            if resolved.exists():
                return str(resolved)

        # Try relative to current working directory
        resolved = Path(path).resolve()
        if resolved.exists():
            return str(resolved)

        # Return original path if can't resolve
        return path

    @staticmethod
    def extract_server_info(
        server_cfg: Dict[str, Any],
        config_file_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Extract server connection information from server config.

        Args:
            server_cfg: Server configuration dictionary.
            config_file_path: Path to config file for resolving
                relative paths.

        Returns:
            Dictionary with server info: host, port, protocol, ssl, auth.
        """
        server_info: Dict[str, Any] = {
            "host": "localhost",
            "port": 8009,
            "protocol": "http",
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        # Determine base directory for resolving relative paths
        base_dir = None
        if config_file_path:
            base_dir = config_file_path.parent

        # Extract server section
        server_section = server_cfg.get("server", {})
        if isinstance(server_section, dict):
            server_info["host"] = server_section.get(
                "host", server_info["host"]
            )
            server_info["port"] = server_section.get(
                "port", server_info["port"]
            )
            server_info["protocol"] = server_section.get(
                "protocol", server_info["protocol"]
            )

        # Extract SSL/TLS configuration
        # For client, prefer registration.ssl (client certs)
        # over server.ssl
        registration_section = server_cfg.get(
            "registration", {}
        )
        registration_ssl = (
            registration_section.get("ssl", {})
            if isinstance(registration_section, dict)
            else {}
        )

        ssl_section = server_cfg.get("ssl", {})
        transport_section = server_cfg.get("transport", {})

        # Use registration SSL (client certs) if available,
        # otherwise server SSL
        if isinstance(registration_ssl, dict) and registration_ssl:
            # Client certs from registration section
            cert_file = (
                registration_ssl.get("cert_file")
                or registration_ssl.get("cert")
            )
            key_file = (
                registration_ssl.get("key_file")
                or registration_ssl.get("key")
            )
            ca_cert_file = (
                registration_ssl.get("ca_cert_file")
                or registration_ssl.get("ca_cert")
                or registration_ssl.get("ca")
            )
            if cert_file or key_file or ca_cert_file:
                server_info["ssl"] = {
                    "enabled": True,
                    "cert_file": ServerConfigGenerator._resolve_path(
                        cert_file, base_dir
                    ),
                    "key_file": ServerConfigGenerator._resolve_path(
                        key_file, base_dir
                    ),
                    "ca_cert_file": ServerConfigGenerator._resolve_path(
                        ca_cert_file, base_dir
                    ),
                    "verify_mode": "CERT_REQUIRED",
                    "check_hostname": registration_ssl.get(
                        "check_hostname", False
                    ),
                }
        elif isinstance(ssl_section, dict) and ssl_section.get("enabled"):
            cert_file = ssl_section.get("cert_file") or ssl_section.get("cert")
            key_file = ssl_section.get("key_file") or ssl_section.get("key")
            ca_cert_file = (
                ssl_section.get("ca_cert_file")
                or ssl_section.get("ca_cert")
                or ssl_section.get("ca")
            )
            server_info["ssl"] = {
                "enabled": True,
                "cert_file": ServerConfigGenerator._resolve_path(
                    cert_file, base_dir
                ),
                "key_file": ServerConfigGenerator._resolve_path(
                    key_file, base_dir
                ),
                "ca_cert_file": ServerConfigGenerator._resolve_path(
                    ca_cert_file, base_dir
                ),
                "verify_mode": (
                    "CERT_REQUIRED"
                    if ssl_section.get("verify_client")
                    else "CERT_NONE"
                ),
                "check_hostname": ssl_section.get("chk_hostname", False),
            }
        elif isinstance(transport_section, dict):
            transport_ssl = transport_section.get("ssl", {})
            if (
                isinstance(transport_ssl, dict)
                and transport_ssl.get("enabled")
            ):
                cert_file = (
                    transport_ssl.get("cert_file")
                    or transport_ssl.get("cert")
                )
                key_file = (
                    transport_ssl.get("key_file")
                    or transport_ssl.get("key")
                )
                ca_cert_file = (
                    transport_ssl.get("ca_cert_file")
                    or transport_ssl.get("ca_cert")
                    or transport_ssl.get("ca")
                )
                server_info["ssl"] = {
                    "enabled": True,
                    "cert_file": ServerConfigGenerator._resolve_path(
                        cert_file, base_dir
                    ),
                    "key_file": ServerConfigGenerator._resolve_path(
                        key_file, base_dir
                    ),
                    "ca_cert_file": ServerConfigGenerator._resolve_path(
                        ca_cert_file, base_dir
                    ),
                    "verify_mode": (
                        "CERT_REQUIRED"
                        if transport_ssl.get("verify_client")
                        else "CERT_NONE"
                    ),
                    "check_hostname": transport_ssl.get("chk_hostname", False),
                }
            elif server_section.get("ssl"):
                ssl = server_section["ssl"]
                if isinstance(ssl, dict):
                    cert_file = ssl.get("cert_file") or ssl.get("cert")
                    key_file = ssl.get("key_file") or ssl.get("key")
                    ca_cert_file = (
                        ssl.get("ca_cert_file")
                        or ssl.get("ca_cert")
                        or ssl.get("ca")
                    )
                    server_info["ssl"] = {
                        "enabled": True,
                        "cert_file": ServerConfigGenerator._resolve_path(
                            cert_file, base_dir
                        ),
                        "key_file": ServerConfigGenerator._resolve_path(
                            key_file, base_dir
                        ),
                        "ca_cert_file": ServerConfigGenerator._resolve_path(
                            ca_cert_file, base_dir
                        ),
                        "verify_mode": "CERT_REQUIRED",
                        "check_hostname": ssl.get("check_hostname", False),
                    }

        # Extract authentication configuration
        auth_section = server_cfg.get("auth", {})
        security_section = server_cfg.get("security", {})
        server_validation = server_cfg.get("server_validation", {})

        # Check for token authentication
        security_enabled = (
            isinstance(security_section, dict)
            and security_section.get("enabled")
        )
        use_token = (
            auth_section.get("use_token", False)
            or server_validation.get("use_token", False)
            or security_enabled
        )

        if use_token:
            tokens = (
                auth_section.get("tokens", {})
                or server_validation.get("tokens", {})
                or (
                    security_section.get("tokens", {})
                    if isinstance(security_section, dict)
                    else {}
                )
            )
            token_header = server_validation.get(
                "auth_header", "X-API-Key"
            )
            # Get first available token
            token = None
            if isinstance(tokens, dict):
                token = tokens.get("default") or (
                    list(tokens.values())[0] if tokens else None
                )

            if token:
                server_info["auth"] = {
                    "method": "api_key",
                    "header": token_header,
                    "api_keys": {"default": token},
                }

        # Check for certificate authentication
        ssl_enabled = server_info["ssl"].get("enabled")
        verify_mode = server_info["ssl"].get("verify_mode")
        if ssl_enabled and verify_mode == "CERT_REQUIRED":
            roles = None
            roles_section = server_cfg.get("roles", {})
            roles_enabled = (
                isinstance(roles_section, dict)
                and roles_section.get("enabled")
            )
            if roles_enabled:
                # Extract roles if available
                roles_config = roles_section.get("config_file")
                if roles_config:
                    try:
                        roles_path = Path(roles_config)
                        if roles_path.exists():
                            with open(roles_path, "r", encoding="utf-8") as f:
                                roles_data = json.load(f)
                                if isinstance(roles_data, dict):
                                    roles = list(roles_data.keys())
                    except Exception:
                        pass

            server_info["auth"] = {
                "method": "certificate",
                "roles": roles,
            }

        return server_info

    @classmethod
    def generate_client_config(
        cls,
        server_config_path: str | Path,
        *,
        override_host: Optional[str] = None,
        override_port: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate client configuration from server configuration file.

        Args:
            server_config_path: Path to server configuration file.
            override_host: Optional host override
                (useful for Docker/localhost).
            override_port: Optional port override.

        Returns:
            Client configuration dictionary compatible with
            ChunkerClient.

        Raises:
            FileNotFoundError: If server config file doesn't exist.
            ValueError: If server config is invalid.
        """
        config_path = Path(server_config_path)
        server_cfg = cls.load_server_config(config_path)
        server_info = cls.extract_server_info(server_cfg, config_path)

        host = override_host or server_info["host"]
        port = override_port or server_info["port"]
        protocol = server_info["protocol"]
        ssl_cfg = server_info["ssl"]
        auth_cfg = server_info["auth"]

        # Generate client config based on protocol and auth
        if protocol == "http" or not ssl_cfg.get("enabled"):
            if auth_cfg.get("method") == "api_key":
                token = auth_cfg.get("api_keys", {}).get("default")
                token_header = auth_cfg.get("header", "X-API-Key")
                roles = auth_cfg.get("roles")
                return ConfigGenerator.http_token(
                    host, port, token, token_header, roles
                )
            return ConfigGenerator.http(host, port)

        ssl_enabled = ssl_cfg.get("enabled")
        verify_mode = ssl_cfg.get("verify_mode")
        if protocol == "https" or (
            ssl_enabled and verify_mode != "CERT_REQUIRED"
        ):
            check_hostname = ssl_cfg.get("check_hostname", False)
            if auth_cfg.get("method") == "api_key":
                token = auth_cfg.get("api_keys", {}).get("default")
                token_header = auth_cfg.get("header", "X-API-Key")
                roles = auth_cfg.get("roles")
                return ConfigGenerator.https_token(
                    host, port, token, token_header, roles, check_hostname
                )
            return ConfigGenerator.https(host, port, check_hostname)

        # mTLS configuration
        if ssl_cfg.get("verify_mode") == "CERT_REQUIRED":
            cert_file = ssl_cfg.get("cert_file")
            key_file = ssl_cfg.get("key_file")
            ca_cert_file = ssl_cfg.get("ca_cert_file")
            check_hostname = ssl_cfg.get("check_hostname", False)
            roles = auth_cfg.get("roles")

            if not cert_file or not key_file or not ca_cert_file:
                raise ValueError(
                    "mTLS requires cert_file, key_file, and "
                    "ca_cert_file in server config"
                )

            return ConfigGenerator.mtls(
                host,
                port,
                cert_file,
                key_file,
                ca_cert_file,
                roles,
                check_hostname,
            )

        # Fallback to HTTP
        return ConfigGenerator.http(host, port)

    @classmethod
    def generate_all_client_configs(
        cls,
        server_config_path: str | Path,
        *,
        override_host: Optional[str] = None,
        override_port: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Generate all possible client config combinations from server config.

        Args:
            server_config_path: Path to server configuration file.
            override_host: Optional host override.
            override_port: Optional port override.

        Returns:
            Dictionary mapping config names to client configurations.
        """
        config_path = Path(server_config_path)
        server_cfg = cls.load_server_config(config_path)
        server_info = cls.extract_server_info(server_cfg, config_path)

        host = override_host or server_info["host"]
        port = override_port or server_info["port"]
        ssl_cfg = server_info["ssl"]
        auth_cfg = server_info["auth"]

        configs: Dict[str, Dict[str, Any]] = {}

        # Always generate HTTP config
        configs["http"] = ConfigGenerator.http(host, port)

        # Generate HTTP + token if token is available
        if auth_cfg.get("method") == "api_key":
            token = auth_cfg.get("api_keys", {}).get("default")
            token_header = auth_cfg.get("header", "X-API-Key")
            roles = auth_cfg.get("roles")
            if token:
                configs["http_token"] = ConfigGenerator.http_token(
                    host, port, token, token_header, roles
                )

        # Generate HTTPS configs if SSL is enabled
        if ssl_cfg.get("enabled"):
            check_hostname = ssl_cfg.get("check_hostname", False)
            configs["https"] = ConfigGenerator.https(
                host, port, check_hostname
            )

            if auth_cfg.get("method") == "api_key":
                token = auth_cfg.get("api_keys", {}).get("default")
                token_header = auth_cfg.get("header", "X-API-Key")
                roles = auth_cfg.get("roles")
                if token:
                    configs["https_token"] = ConfigGenerator.https_token(
                        host, port, token, token_header, roles, check_hostname
                    )

        # Generate mTLS config if certificates are available
        if ssl_cfg.get("verify_mode") == "CERT_REQUIRED":
            cert_file = ssl_cfg.get("cert_file")
            key_file = ssl_cfg.get("key_file")
            ca_cert_file = ssl_cfg.get("ca_cert_file")
            check_hostname = ssl_cfg.get("check_hostname", False)
            roles = auth_cfg.get("roles")

            if cert_file and key_file and ca_cert_file:
                configs["mtls"] = ConfigGenerator.mtls(
                    host,
                    port,
                    cert_file,
                    key_file,
                    ca_cert_file,
                    roles,
                    check_hostname,
                )

        return configs
