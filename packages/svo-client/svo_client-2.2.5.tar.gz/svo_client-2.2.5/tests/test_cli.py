"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests for CLI commands.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from svo_client.cli import _build_config, _roles_from_arg
from svo_client.config_tools import ConfigValidator


class TestCLIHelpers:
    """Test CLI helper functions."""

    def test_roles_from_arg(self):
        """Test parsing roles from argument."""
        assert _roles_from_arg("admin,user") == ["admin", "user"]
        assert _roles_from_arg("admin, user, reader") == ["admin", "user", "reader"]
        assert _roles_from_arg(None) is None
        assert _roles_from_arg("") is None
        assert _roles_from_arg("  ") is None

    def test_build_config_http(self):
        """Test building HTTP config."""
        class Args:
            mode = "http"
            host = "localhost"
            port = 8009
            token = None
            token_header = "X-API-Key"
            roles = None
            cert = None
            key = None
            ca = None
            check_hostname = False

        config = _build_config(Args())
        assert config["server"]["host"] == "localhost"
        assert config["server"]["port"] == 8009
        assert config["ssl"]["enabled"] is False
        assert config["auth"]["method"] == "none"

    def test_build_config_http_token(self):
        """Test building HTTP config with token."""
        class Args:
            mode = "http_token"
            host = "localhost"
            port = 8009
            token = "test-token"
            token_header = "X-API-Key"
            roles = None
            cert = None
            key = None
            ca = None
            check_hostname = False

        config = _build_config(Args())
        assert config["auth"]["method"] == "api_key"
        assert config["auth"]["api_keys"]["default"] == "test-token"

    def test_build_config_mtls(self):
        """Test building mTLS config."""
        class Args:
            mode = "mtls"
            host = "localhost"
            port = 8009
            token = None
            token_header = "X-API-Key"
            roles = None
            cert = "cert.crt"
            key = "key.key"
            ca = "ca.crt"
            check_hostname = False

        config = _build_config(Args())
        assert config["ssl"]["enabled"] is True
        assert config["ssl"]["verify_mode"] == "CERT_REQUIRED"
        assert config["auth"]["method"] == "certificate"

    def test_build_config_mtls_token(self):
        """Test building mTLS config with token."""
        class Args:
            mode = "mtls_token"
            host = "localhost"
            port = 8009
            token = "test-token"
            token_header = "X-API-Key"
            roles = None
            cert = "cert.crt"
            key = "key.key"
            ca = "ca.crt"
            check_hostname = False

        config = _build_config(Args())
        assert config["ssl"]["enabled"] is True
        assert config["auth"]["method"] == "api_key"
        assert config["auth"]["api_keys"]["default"] == "test-token"

    def test_build_config_missing_mtls_certs(self):
        """Test building mTLS config without certificates."""
        class Args:
            mode = "mtls"
            host = "localhost"
            port = 8009
            token = None
            token_header = "X-API-Key"
            roles = None
            cert = None
            key = None
            ca = None
            check_hostname = False

        with pytest.raises(SystemExit, match="cert, --key, --ca required"):
            _build_config(Args())

    def test_build_config_missing_token(self):
        """Test building config with token mode but no token."""
        class Args:
            mode = "http_token"
            host = "localhost"
            port = 8009
            token = None
            token_header = "X-API-Key"
            roles = None
            cert = None
            key = None
            ca = None
            check_hostname = False

        with pytest.raises(SystemExit, match="token is required"):
            _build_config(Args())

    def test_build_config_with_config_file(self):
        """Test building config with config file."""
        config = {
            "server": {"host": "file-host", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            class Args:
                mode = "http"
                host = "cli-host"
                port = 8000
                token = None
                token_header = "X-API-Key"
                roles = None
                cert = None
                key = None
                ca = None
                check_hostname = False
                config = config_path

            built_config = _build_config(Args())
            # CLI should override file config
            assert built_config["server"]["host"] == "cli-host"
            assert built_config["server"]["port"] == 8000
        finally:
            Path(config_path).unlink()

    def test_build_config_https_token(self):
        """Test building HTTPS config with token."""
        class Args:
            mode = "https_token"
            host = "localhost"
            port = 8009
            token = "test-token"
            token_header = "Authorization"
            roles = "admin,user"
            cert = None
            key = None
            ca = None
            check_hostname = True

        config = _build_config(Args())
        assert config["ssl"]["enabled"] is True
        assert config["auth"]["method"] == "api_key"
        assert config["auth"]["header"] == "Authorization"
        assert config["auth"]["api_keys"]["default"] == "test-token"

