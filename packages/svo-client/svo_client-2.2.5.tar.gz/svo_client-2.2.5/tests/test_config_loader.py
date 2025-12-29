"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests for configuration loader with priority support.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from svo_client.config_loader import ConfigLoader


class TestConfigLoader:
    """Test ConfigLoader class."""

    def test_load_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("SVO_HOST", "env-host")
        monkeypatch.setenv("SVO_PORT", "9000")
        monkeypatch.setenv("SVO_TOKEN", "env-token")

        config = ConfigLoader.load_from_env()

        assert config["server"]["host"] == "env-host"
        assert config["server"]["port"] == 9000
        assert config["auth"]["api_keys"]["default"] == "env-token"

    def test_load_from_env_mtls(self, monkeypatch):
        """Test loading mTLS config from environment variables."""
        monkeypatch.setenv("SVO_HOST", "localhost")
        monkeypatch.setenv("SVO_PORT", "8009")
        monkeypatch.setenv("SVO_CERT", "cert.crt")
        monkeypatch.setenv("SVO_KEY", "key.key")
        monkeypatch.setenv("SVO_CA", "ca.crt")

        config = ConfigLoader.load_from_env()

        assert config["ssl"]["enabled"] is True
        assert config["ssl"]["verify_mode"] == "CERT_REQUIRED"

    def test_load_from_file(self):
        """Test loading configuration from file."""
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
            loaded = ConfigLoader.load_from_file(config_path)
            assert loaded == config
        finally:
            Path(config_path).unlink()

    def test_load_from_file_not_found(self):
        """Test loading non-existent config file."""
        result = ConfigLoader.load_from_file("nonexistent.json")
        assert result is None

    def test_load_from_file_env_var(self, monkeypatch):
        """Test loading config file from environment variable."""
        config = {
            "server": {"host": "env-file-host", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            monkeypatch.setenv("SVO_CONFIG", config_path)
            loaded = ConfigLoader.load_from_file()
            assert loaded == config
        finally:
            Path(config_path).unlink()

    def test_merge_configs(self):
        """Test merging multiple configurations."""
        config1 = {
            "server": {"host": "host1", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        config2 = {
            "server": {"host": "host2"},
            "ssl": {"enabled": True},
        }

        config3 = {
            "auth": {"method": "api_key", "api_keys": {"default": "token"}},
        }

        merged = ConfigLoader.merge_configs(config1, config2, config3)

        # config3 has highest priority
        assert merged["server"]["host"] == "host2"
        assert merged["server"]["port"] == 8009  # From config1
        assert merged["ssl"]["enabled"] is True  # From config2
        assert merged["auth"]["method"] == "api_key"  # From config3

    def test_resolve_config_priority(self, monkeypatch):
        """Test configuration priority: CLI > env > file."""
        # File config (lowest priority)
        file_config = {
            "server": {"host": "file-host", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(file_config, f)
            config_path = f.name

        try:
            # Env config (middle priority)
            monkeypatch.setenv("SVO_HOST", "env-host")
            monkeypatch.setenv("SVO_PORT", "9000")

            # CLI/API config (highest priority)
            resolved = ConfigLoader.resolve_config(
                host="cli-host",
                port=8000,
                config_file=config_path,
            )

            # CLI should override env and file
            assert resolved["server"]["host"] == "cli-host"
            assert resolved["server"]["port"] == 8000
        finally:
            Path(config_path).unlink()

    def test_resolve_config_env_overrides_file(self, monkeypatch):
        """Test environment variables override config file."""
        file_config = {
            "server": {"host": "file-host", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(file_config, f)
            config_path = f.name

        try:
            monkeypatch.setenv("SVO_HOST", "env-host")
            monkeypatch.setenv("SVO_PORT", "9000")

            resolved = ConfigLoader.resolve_config(
                config_file=config_path,
            )

            # Env should override file
            assert resolved["server"]["host"] == "env-host"
            assert resolved["server"]["port"] == 9000
        finally:
            Path(config_path).unlink()

    def test_resolve_config_prebuilt_has_priority(self):
        """Test pre-built config has highest priority."""
        prebuilt = {
            "server": {"host": "prebuilt-host", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        resolved = ConfigLoader.resolve_config(config=prebuilt)

        assert resolved == prebuilt

    def test_resolve_config_with_token(self, monkeypatch):
        """Test resolving config with token from different sources."""
        monkeypatch.setenv("SVO_TOKEN", "env-token")

        # CLI token should override env token
        resolved = ConfigLoader.resolve_config(token="cli-token")

        assert resolved["auth"]["api_keys"]["default"] == "cli-token"

    def test_resolve_config_with_certificates(self, monkeypatch):
        """Test resolving config with certificates."""
        monkeypatch.setenv("SVO_CERT", "env-cert.crt")
        monkeypatch.setenv("SVO_KEY", "env-key.key")
        monkeypatch.setenv("SVO_CA", "env-ca.crt")

        # CLI certs should override env certs
        resolved = ConfigLoader.resolve_config(
            cert="cli-cert.crt",
            key="cli-key.key",
            ca="cli-ca.crt",
        )

        assert resolved["ssl"]["cert_file"] == "cli-cert.crt"
        assert resolved["ssl"]["key_file"] == "cli-key.key"
        assert resolved["ssl"]["ca_cert_file"] == "cli-ca.crt"

