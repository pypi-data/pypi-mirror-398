"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests for client configuration generator.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from svo_client.client_config_generator import ClientConfigGenerator
from svo_client.config_tools import ConfigValidator


class TestClientConfigGenerator:
    """Test ClientConfigGenerator class."""

    def test_generate_from_params_http(self):
        """Test generating HTTP config from parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_params(
                host="localhost",
                port=8009,
                config_name="test_config.json",
                output_dir=tmpdir,
            )

            assert output_path.exists()
            config = json.loads(output_path.read_text())
            assert config["server"]["host"] == "localhost"
            assert config["server"]["port"] == 8009
            assert config["ssl"]["enabled"] is False
            assert config["auth"]["method"] == "none"

    def test_generate_from_params_https(self):
        """Test generating HTTPS config from parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_params(
                host="localhost",
                port=8009,
                cert="cert.crt",
                key="key.key",
                ca="ca.crt",
                check_hostname=True,
                config_name="test_config.json",
                output_dir=tmpdir,
            )

            config = json.loads(output_path.read_text())
            assert config["ssl"]["enabled"] is True
            assert config["ssl"]["verify_mode"] == "CERT_REQUIRED"
            assert config["ssl"]["check_hostname"] is True

    def test_generate_from_params_mtls(self):
        """Test generating mTLS config from parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_params(
                host="localhost",
                port=8009,
                cert="cert.crt",
                key="key.key",
                ca="ca.crt",
                config_name="test_config.json",
                output_dir=tmpdir,
            )

            config = json.loads(output_path.read_text())
            assert config["ssl"]["enabled"] is True
            assert config["ssl"]["verify_mode"] == "CERT_REQUIRED"
            assert config["auth"]["method"] == "certificate"

    def test_generate_from_params_with_token(self):
        """Test generating config with token authentication."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_params(
                host="localhost",
                port=8009,
                token="test-token",
                token_header="Authorization",
                config_name="test_config.json",
                output_dir=tmpdir,
            )

            config = json.loads(output_path.read_text())
            assert config["auth"]["method"] == "api_key"
            assert config["auth"]["header"] == "Authorization"
            assert config["auth"]["api_keys"]["default"] == "test-token"

    def test_generate_from_params_mtls_with_token(self):
        """Test generating mTLS config with token."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_params(
                host="localhost",
                port=8009,
                cert="cert.crt",
                key="key.key",
                ca="ca.crt",
                token="test-token",
                config_name="test_config.json",
                output_dir=tmpdir,
            )

            config = json.loads(output_path.read_text())
            assert config["ssl"]["enabled"] is True
            assert config["ssl"]["verify_mode"] == "CERT_REQUIRED"
            # mTLS with token: method should be api_key, token in api_keys
            assert config["auth"]["method"] == "api_key"
            assert config["auth"]["api_keys"]["default"] == "test-token"

    def test_generate_from_params_with_roles(self):
        """Test generating config with roles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_params(
                host="localhost",
                port=8009,
                token="test-token",
                roles=["admin", "user"],
                config_name="test_config.json",
                output_dir=tmpdir,
            )

            config = json.loads(output_path.read_text())
            assert config["auth"]["roles"] == ["admin", "user"]

    def test_generate_from_env(self, monkeypatch):
        """Test generating config from environment variables."""
        monkeypatch.setenv("SVO_HOST", "env-host")
        monkeypatch.setenv("SVO_PORT", "9000")
        monkeypatch.setenv("SVO_TOKEN", "env-token")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_env(
                config_name="test_config.json",
                output_dir=tmpdir,
            )

            config = json.loads(output_path.read_text())
            assert config["server"]["host"] == "env-host"
            assert config["server"]["port"] == 9000
            assert config["auth"]["api_keys"]["default"] == "env-token"

    def test_generate_from_env_mtls(self, monkeypatch):
        """Test generating mTLS config from environment variables."""
        monkeypatch.setenv("SVO_HOST", "localhost")
        monkeypatch.setenv("SVO_PORT", "8009")
        monkeypatch.setenv("SVO_CERT", "cert.crt")
        monkeypatch.setenv("SVO_KEY", "key.key")
        monkeypatch.setenv("SVO_CA", "ca.crt")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_env(
                config_name="test_config.json",
                output_dir=tmpdir,
            )

            config = json.loads(output_path.read_text())
            assert config["ssl"]["enabled"] is True
            assert config["ssl"]["verify_mode"] == "CERT_REQUIRED"

    def test_save_config(self):
        """Test saving configuration to file."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.save_config(
                config, "test_config.json", tmpdir
            )

            assert output_path.exists()
            loaded = json.loads(output_path.read_text())
            assert loaded == config

    def test_load_config(self):
        """Test loading configuration from file."""
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
            loaded = ClientConfigGenerator.load_config(config_path)
            assert loaded == config
        finally:
            Path(config_path).unlink()

    def test_load_config_not_found(self):
        """Test loading non-existent config file."""
        with pytest.raises(FileNotFoundError):
            ClientConfigGenerator.load_config("nonexistent.json")

    def test_load_config_invalid_json(self):
        """Test loading invalid JSON file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("invalid json")
            config_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                ClientConfigGenerator.load_config(config_path)
        finally:
            Path(config_path).unlink()

