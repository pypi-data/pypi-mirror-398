"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Configuration utilities for ChunkerClient.
"""

from typing import Any, Dict, Optional


def generate_config(
    *,
    host: str,
    port: int,
    cert: Optional[str],
    key: Optional[str],
    ca: Optional[str],
    token: Optional[str],
    token_header: str,
) -> Dict[str, Any]:
    """Generate client configuration without external dependencies.

    Args:
        host: Server hostname or IP address.
        port: Server port number.
        cert: Path to client certificate file (for mTLS).
        key: Path to client private key file (for mTLS).
        ca: Path to CA certificate file (for mTLS).
        token: API token for authentication.
        token_header: HTTP header name for token authentication.

    Returns:
        Configuration dictionary.
    """
    cfg: Dict[str, Any] = {
        "server": {
            "host": host,
            "port": port,
        },
        "ssl": {},
        "auth": {},
    }
    
    # Configure SSL/mTLS
    if cert or key or ca:
        cfg["ssl"] = {
            "enabled": True,
            "cert_file": cert,
            "key_file": key,
            "ca_cert_file": ca,
            "verify_mode": "CERT_REQUIRED" if ca else "CERT_NONE",
            "check_hostname": False,  # Default for Docker/localhost
        }
    else:
        cfg["ssl"] = {
            "enabled": False,
        }
    
    # Configure authentication
    if token:
        cfg["auth"] = {
            "method": "api_key",
            "header": token_header,
            "api_keys": {
                "default": token,
            },
        }
        # If token is used, enable HTTPS if not already enabled
        if not cfg["ssl"].get("enabled"):
            cfg["ssl"] = {
                "enabled": True,
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
            }
    
    return cfg


def config_to_client_kwargs(
    cfg: Dict[str, Any], *, check_hostname: bool
) -> tuple[str, Dict[str, Any]]:
    """Convert configuration dict to JsonRpcClient kwargs.

    Args:
        cfg: Configuration dictionary.
        check_hostname: Whether to verify hostname in SSL certificate.

    Returns:
        Tuple of (protocol, client_kwargs) for JsonRpcClient initialization.
    """
    server = cfg.get("server", {})
    ssl_cfg = cfg.get("ssl", {}) or {}
    auth_cfg = cfg.get("auth", {}) or {}

    protocol = "http"
    if ssl_cfg.get("enabled"):
        verify_mode = ssl_cfg.get("verify_mode")
        protocol = "mtls" if verify_mode == "CERT_REQUIRED" else "https"

    token_header = auth_cfg.get("header", "X-API-Key")
    api_keys = auth_cfg.get("api_keys", {}) or {}
    token = api_keys.get("default") if api_keys else None

    client_kwargs: Dict[str, Any] = {
        "protocol": protocol,
        "host": server.get("host", "localhost"),
        "port": server.get("port", 8009),
    }

    if protocol in ("https", "mtls"):
        client_kwargs["check_hostname"] = check_hostname
        if ssl_cfg.get("enabled"):
            if ssl_cfg.get("cert_file"):
                client_kwargs["cert"] = ssl_cfg["cert_file"]
            if ssl_cfg.get("key_file"):
                client_kwargs["key"] = ssl_cfg["key_file"]
            if ssl_cfg.get("ca_cert_file"):
                client_kwargs["ca"] = ssl_cfg["ca_cert_file"]

    if token:
        client_kwargs["token"] = token
        client_kwargs["token_header"] = token_header

    return protocol, client_kwargs

