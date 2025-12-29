"""
Tests for config_utils module.
"""

import pytest

from svo_client.config_utils import config_to_client_kwargs, generate_config


def test_generate_config_http():
    """Test generating HTTP configuration."""
    cfg = generate_config(
        host="localhost",
        port=8009,
        cert=None,
        key=None,
        ca=None,
        token=None,
        token_header="X-API-Key",
    )
    assert cfg["server"]["host"] == "localhost"
    assert cfg["server"]["port"] == 8009
    assert cfg["ssl"]["enabled"] is False
    assert cfg["auth"] == {}


def test_generate_config_mtls():
    """Test generating mTLS configuration."""
    cfg = generate_config(
        host="localhost",
        port=8009,
        cert="cert.pem",
        key="key.pem",
        ca="ca.pem",
        token=None,
        token_header="X-API-Key",
    )
    assert cfg["ssl"]["enabled"] is True
    assert cfg["ssl"]["cert_file"] == "cert.pem"
    assert cfg["ssl"]["key_file"] == "key.pem"
    assert cfg["ssl"]["ca_cert_file"] == "ca.pem"
    assert cfg["ssl"]["verify_mode"] == "CERT_REQUIRED"


def test_generate_config_with_token():
    """Test generating configuration with token."""
    cfg = generate_config(
        host="localhost",
        port=8009,
        cert=None,
        key=None,
        ca=None,
        token="test-token",
        token_header="X-API-Key",
    )
    assert cfg["auth"]["method"] == "api_key"
    assert cfg["auth"]["header"] == "X-API-Key"
    assert cfg["auth"]["api_keys"]["default"] == "test-token"
    assert cfg["ssl"]["enabled"] is True  # Token enables HTTPS


def test_config_to_client_kwargs_http():
    """Test converting HTTP config to client kwargs."""
    cfg = {
        "server": {"host": "localhost", "port": 8009},
        "ssl": {"enabled": False},
        "auth": {},
    }
    protocol, kwargs = config_to_client_kwargs(cfg, check_hostname=False)
    assert protocol == "http"
    assert kwargs["host"] == "localhost"
    assert kwargs["port"] == 8009


def test_config_to_client_kwargs_https():
    """Test converting HTTPS config to client kwargs."""
    cfg = {
        "server": {"host": "localhost", "port": 8009},
        "ssl": {"enabled": True, "verify_mode": "CERT_NONE"},
        "auth": {},
    }
    protocol, kwargs = config_to_client_kwargs(cfg, check_hostname=True)
    assert protocol == "https"
    assert kwargs["check_hostname"] is True


def test_config_to_client_kwargs_mtls():
    """Test converting mTLS config to client kwargs."""
    cfg = {
        "server": {"host": "localhost", "port": 8009},
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "cert_file": "cert.pem",
            "key_file": "key.pem",
            "ca_cert_file": "ca.pem",
        },
        "auth": {},
    }
    protocol, kwargs = config_to_client_kwargs(cfg, check_hostname=False)
    assert protocol == "mtls"
    assert kwargs["cert"] == "cert.pem"
    assert kwargs["key"] == "key.pem"
    assert kwargs["ca"] == "ca.pem"


def test_config_to_client_kwargs_with_token():
    """Test converting config with token to client kwargs."""
    cfg = {
        "server": {"host": "localhost", "port": 8009},
        "ssl": {"enabled": False},
        "auth": {
            "method": "api_key",
            "header": "X-API-Key",
            "api_keys": {"default": "test-token"},
        },
    }
    protocol, kwargs = config_to_client_kwargs(cfg, check_hostname=False)
    assert kwargs["token"] == "test-token"
    assert kwargs["token_header"] == "X-API-Key"

