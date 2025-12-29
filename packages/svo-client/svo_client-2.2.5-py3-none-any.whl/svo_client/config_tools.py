"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Configuration generator and validator for ChunkerClient.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ConfigValidator:
    """Validate client configuration structure."""

    @staticmethod
    def validate(cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration dictionary.

        Args:
            cfg: Configuration dictionary to validate.

        Returns:
            Validated configuration dictionary.

        Raises:
            ValueError: If configuration is invalid.
        """
        if not isinstance(cfg, dict):
            raise ValueError("Config must be a dict")

        server = cfg.get("server", {})
        if not isinstance(server, dict):
            raise ValueError("Config.server must be a dict")
        host = server.get("host")
        port = server.get("port")
        if not host or not isinstance(host, str):
            raise ValueError("Config.server.host is required")
        if not isinstance(port, int):
            raise ValueError("Config.server.port must be int")

        ssl_cfg = cfg.get("ssl", {}) or {}
        if not isinstance(ssl_cfg, dict):
            raise ValueError("Config.ssl must be a dict")
        if ssl_cfg.get("enabled"):
            if ssl_cfg.get("verify_mode") == "CERT_REQUIRED":
                for field in ("cert_file", "key_file", "ca_cert_file"):
                    if not ssl_cfg.get(field):
                        raise ValueError(f"SSL requires {field}")

        auth_cfg = cfg.get("auth", {}) or {}
        if not isinstance(auth_cfg, dict):
            raise ValueError("Config.auth must be a dict")
        method = auth_cfg.get("method", "none")
        if method == "api_key":
            api_keys = auth_cfg.get("api_keys") or {}
            if not api_keys:
                raise ValueError("api_key auth requires api_keys")
        if (
            method == "certificate"
            and ssl_cfg.get("verify_mode") != "CERT_REQUIRED"
        ):
            raise ValueError(
                "certificate auth requires mTLS (verify_mode=CERT_REQUIRED)"
            )

        return cfg


class ConfigGenerator:
    """Generate configs for all supported protocols/modes."""

    @staticmethod
    def _base(host: str, port: int, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Create base server configuration.

        Args:
            host: Server hostname or IP.
            port: Server port number.
            timeout: Optional request timeout in seconds.

        Returns:
            Base configuration dictionary with server settings.
        """
        cfg = {"server": {"host": host, "port": port}}
        if timeout is not None:
            cfg["timeout"] = timeout
        return cfg

    @staticmethod
    def _ssl(
        enabled: bool,
        cert: Optional[str] = None,
        key: Optional[str] = None,
        ca: Optional[str] = None,
        check_hostname: bool = False,
        verify_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create SSL/TLS configuration.

        Args:
            enabled: Whether SSL is enabled.
            cert: Path to certificate file.
            key: Path to private key file.
            ca: Path to CA certificate file.
            check_hostname: Whether to verify hostname.
            verify_mode: SSL verification mode.

        Returns:
            SSL configuration dictionary.
        """
        cfg: Dict[str, Any] = {
            "enabled": enabled,
            "check_hostname": check_hostname,
        }
        if verify_mode:
            cfg["verify_mode"] = verify_mode
        if cert:
            cfg["cert_file"] = cert
        if key:
            cfg["key_file"] = key
        if ca:
            cfg["ca_cert_file"] = ca
        return cfg

    @staticmethod
    def _auth_none() -> Dict[str, Any]:
        """Create no-authentication configuration.

        Returns:
            Authentication configuration dictionary with method 'none'.
        """
        return {"method": "none"}

    @staticmethod
    def _auth_api_key(
        token: str, header: str, roles: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Create API key authentication configuration.

        Args:
            token: API token.
            header: HTTP header name for token.
            roles: Optional list of roles.

        Returns:
            Authentication configuration dictionary with API key method.
        """
        cfg: Dict[str, Any] = {
            "method": "api_key",
            "header": header,
            "api_keys": {"default": token},
        }
        if roles:
            cfg["roles"] = roles
        return cfg

    @staticmethod
    def _auth_cert(roles: Optional[List[str]]) -> Dict[str, Any]:
        """Create certificate-based authentication configuration.

        Args:
            roles: Optional list of roles.

        Returns:
            Authentication configuration dictionary with certificate method.
        """
        cfg: Dict[str, Any] = {"method": "certificate"}
        if roles:
            cfg["roles"] = roles
        return cfg

    @classmethod
    def http(cls, host: str, port: int) -> Dict[str, Any]:
        """Generate HTTP configuration (no SSL, no auth).

        Args:
            host: Server hostname or IP.
            port: Server port number.

        Returns:
            Complete configuration dictionary for HTTP.
        """
        cfg = cls._base(host, port)
        cfg["ssl"] = cls._ssl(enabled=False)
        cfg["auth"] = cls._auth_none()
        return cfg

    @classmethod
    def http_token(
        cls, host: str, port: int, token: str, header: str, roles: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Generate HTTP configuration with token authentication.

        Args:
            host: Server hostname or IP.
            port: Server port number.
            token: API token.
            header: HTTP header name for token.
            roles: Optional list of roles.

        Returns:
            Complete configuration dictionary for HTTP with token auth.
        """
        cfg = cls._base(host, port)
        cfg["ssl"] = cls._ssl(enabled=False)
        cfg["auth"] = cls._auth_api_key(token, header, roles)
        return cfg

    @classmethod
    def https(cls, host: str, port: int, check_hostname: bool) -> Dict[str, Any]:
        """Generate HTTPS configuration (SSL, no auth).

        Args:
            host: Server hostname or IP.
            port: Server port number.
            check_hostname: Whether to verify hostname in certificate.

        Returns:
            Complete configuration dictionary for HTTPS.
        """
        cfg = cls._base(host, port)
        cfg["ssl"] = cls._ssl(enabled=True, check_hostname=check_hostname)
        cfg["auth"] = cls._auth_none()
        return cfg

    @classmethod
    def https_token(
        cls,
        host: str,
        port: int,
        token: str,
        header: str,
        roles: Optional[List[str]],
        check_hostname: bool,
    ) -> Dict[str, Any]:
        """Generate HTTPS configuration with token authentication.

        Args:
            host: Server hostname or IP.
            port: Server port number.
            token: API token.
            header: HTTP header name for token.
            roles: Optional list of roles.
            check_hostname: Whether to verify hostname in certificate.

        Returns:
            Complete configuration dictionary for HTTPS with token auth.
        """
        cfg = cls._base(host, port)
        cfg["ssl"] = cls._ssl(enabled=True, check_hostname=check_hostname)
        cfg["auth"] = cls._auth_api_key(token, header, roles)
        return cfg

    @classmethod
    def mtls(
        cls,
        host: str,
        port: int,
        cert: str,
        key: str,
        ca: str,
        roles: Optional[List[str]],
        check_hostname: bool,
    ) -> Dict[str, Any]:
        """Generate mTLS configuration with certificate authentication.

        Args:
            host: Server hostname or IP.
            port: Server port number.
            cert: Path to client certificate file.
            key: Path to client private key file.
            ca: Path to CA certificate file.
            roles: Optional list of roles.
            check_hostname: Whether to verify hostname in certificate.

        Returns:
            Complete configuration dictionary for mTLS.
        """
        cfg = cls._base(host, port)
        cfg["ssl"] = cls._ssl(
            enabled=True,
            cert=cert,
            key=key,
            ca=ca,
            check_hostname=check_hostname,
            verify_mode="CERT_REQUIRED",
        )
        cfg["auth"] = cls._auth_cert(roles)
        return cfg

    @classmethod
    def generate_all_configs(
        cls,
        host: str,
        port: int,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        token: Optional[str] = None,
        token_header: str = "X-API-Key",
        roles: Optional[List[str]] = None,
        check_hostname: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """Generate all possible config combinations."""
        configs: Dict[str, Dict[str, Any]] = {}
        
        # HTTP
        configs["http"] = cls.http(host, port)
        
        # HTTP + token
        if token:
            configs["http_token"] = cls.http_token(host, port, token, token_header, roles)
        
        # HTTPS
        configs["https"] = cls.https(host, port, check_hostname)
        
        # HTTPS + token
        if token:
            configs["https_token"] = cls.https_token(host, port, token, token_header, roles, check_hostname)
        
        # mTLS
        if cert_file and key_file and ca_cert_file:
            configs["mtls"] = cls.mtls(host, port, cert_file, key_file, ca_cert_file, roles, check_hostname)
        
        return configs





