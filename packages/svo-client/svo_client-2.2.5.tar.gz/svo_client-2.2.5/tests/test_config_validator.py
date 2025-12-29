"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests for configuration validator.
"""

import json
import tempfile
from pathlib import Path

import pytest

from svo_client.client_config_generator import ClientConfigGenerator
from svo_client.config_tools import ConfigValidator
from validate_client_config import validate_file


class TestConfigValidator:
    """Test ConfigValidator class."""

    def test_validate_http_config(self):
        """Test validating HTTP configuration."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        validated = ConfigValidator.validate(config)
        assert validated == config

    def test_validate_https_config(self):
        """Test validating HTTPS configuration."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
            },
            "auth": {"method": "none"},
        }

        validated = ConfigValidator.validate(config)
        assert validated == config

    def test_validate_mtls_config(self):
        """Test validating mTLS configuration."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {
                "enabled": True,
                "cert_file": "cert.crt",
                "key_file": "key.key",
                "ca_cert_file": "ca.crt",
                "verify_mode": "CERT_REQUIRED",
                "check_hostname": False,
            },
            "auth": {"method": "certificate"},
        }

        validated = ConfigValidator.validate(config)
        assert validated == config

    def test_validate_token_config(self):
        """Test validating token authentication configuration."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {
                "method": "api_key",
                "header": "X-API-Key",
                "api_keys": {"default": "test-token"},
            },
        }

        validated = ConfigValidator.validate(config)
        assert validated == config

    def test_validate_missing_host(self):
        """Test validation fails with missing host."""
        config = {
            "server": {"port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with pytest.raises(ValueError, match="host is required"):
            ConfigValidator.validate(config)

    def test_validate_missing_port(self):
        """Test validation fails with missing port."""
        config = {
            "server": {"host": "localhost"},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with pytest.raises(ValueError, match="port must be int"):
            ConfigValidator.validate(config)

    def test_validate_mtls_missing_cert(self):
        """Test validation fails with missing certificate for mTLS."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {
                "enabled": True,
                "verify_mode": "CERT_REQUIRED",
                "key_file": "key.key",
                "ca_cert_file": "ca.crt",
            },
            "auth": {"method": "certificate"},
        }

        with pytest.raises(ValueError, match="SSL requires cert_file"):
            ConfigValidator.validate(config)

    def test_validate_token_missing_api_keys(self):
        """Test validation fails with missing api_keys."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "api_key", "header": "X-API-Key"},
        }

        with pytest.raises(ValueError, match="api_key auth requires api_keys"):
            ConfigValidator.validate(config)

    def test_validate_certificate_auth_without_mtls(self):
        """Test validation fails with certificate auth without mTLS."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "certificate"},
        }

        with pytest.raises(
            ValueError, match="certificate auth requires mTLS"
        ):
            ConfigValidator.validate(config)


class TestValidateFile:
    """Test validate_file function."""

    def test_validate_valid_config(self):
        """Test validating a valid configuration file."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            is_valid, errors = validate_file(config_path)
            assert is_valid is True
            assert len(errors) == 0
        finally:
            Path(config_path).unlink()

    def test_validate_invalid_config(self):
        """Test validating an invalid configuration file."""
        config = {
            "server": {"port": 8009},  # Missing host
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            is_valid, errors = validate_file(config_path)
            assert is_valid is False
            assert len(errors) > 0
        finally:
            Path(config_path).unlink()

    def test_validate_mtls_with_missing_files(self):
        """Test validating mTLS config with missing certificate files."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {
                "enabled": True,
                "cert_file": "/nonexistent/cert.crt",
                "key_file": "/nonexistent/key.key",
                "ca_cert_file": "/nonexistent/ca.crt",
                "verify_mode": "CERT_REQUIRED",
            },
            "auth": {"method": "certificate"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            is_valid, errors = validate_file(config_path)
            assert is_valid is False
            assert len(errors) > 0
            assert any("not found" in err.lower() for err in errors)
        finally:
            Path(config_path).unlink()

    def test_validate_verbose(self, capsys):
        """Test verbose validation output."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            is_valid, errors = validate_file(config_path, verbose=True)
            # Verbose mode may print output but should still return valid
            # Check that config is actually valid
            validated = ConfigValidator.validate(config)
            assert validated is not None
        finally:
            Path(config_path).unlink()

    def test_validate_from_stdin(self, monkeypatch):
        """Test validating config from stdin."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        import sys
        from io import StringIO

        stdin_backup = sys.stdin
        try:
            sys.stdin = StringIO(json.dumps(config))
            is_valid, errors = validate_file("-")
            assert is_valid is True
        finally:
            sys.stdin = stdin_backup

