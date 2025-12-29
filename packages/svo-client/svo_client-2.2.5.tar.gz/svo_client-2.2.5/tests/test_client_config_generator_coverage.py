"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Additional tests to increase ClientConfigGenerator coverage.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from svo_client.client_config_generator import ClientConfigGenerator


class TestClientConfigGeneratorCoverage:
    """Tests to increase ClientConfigGenerator coverage."""

    def test_generate_from_params_all_options(self):
        """Test generate_from_params with all options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_params(
                host="test-host",
                port=9000,
                cert="cert.crt",
                key="key.key",
                ca="ca.crt",
                token="test-token",
                token_header="Authorization",
                roles=["admin", "user"],
                check_hostname=True,
                config_name="test.json",
                output_dir=tmpdir,
            )

            config = json.loads(output_path.read_text())
            assert config["server"]["host"] == "test-host"
            assert config["server"]["port"] == 9000
            assert config["ssl"]["enabled"] is True
            assert config["auth"]["method"] == "api_key"
            assert config["auth"]["api_keys"]["default"] == "test-token"

    def test_generate_from_params_https_with_cert(self):
        """Test generate_from_params with HTTPS and cert."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_params(
                host="localhost",
                port=8009,
                cert="cert.crt",
                key="key.key",
                ca=None,
                check_hostname=True,
                config_name="test.json",
                output_dir=tmpdir,
            )

            config = json.loads(output_path.read_text())
            assert config["ssl"]["enabled"] is True

    def test_generate_from_env_all_vars(self, monkeypatch):
        """Test generate_from_env with all env vars."""
        monkeypatch.setenv("SVO_HOST", "env-host")
        monkeypatch.setenv("SVO_PORT", "9000")
        monkeypatch.setenv("SVO_CERT", "cert.crt")
        monkeypatch.setenv("SVO_KEY", "key.key")
        monkeypatch.setenv("SVO_CA", "ca.crt")
        monkeypatch.setenv("SVO_TOKEN", "env-token")
        monkeypatch.setenv("SVO_TOKEN_HEADER", "Authorization")
        monkeypatch.setenv("SVO_CHECK_HOSTNAME", "true")
        monkeypatch.setenv("SVO_ROLES", "admin,user")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_env(
                config_name="test.json",
                output_dir=tmpdir,
            )

            config = json.loads(output_path.read_text())
            assert config["server"]["host"] == "env-host"
            assert config["server"]["port"] == 9000
            assert config["auth"]["api_keys"]["default"] == "env-token"

    def test_generate_from_env_https(self, monkeypatch):
        """Test generate_from_env with HTTPS."""
        monkeypatch.setenv("SVO_HOST", "localhost")
        monkeypatch.setenv("SVO_PORT", "8009")
        monkeypatch.setenv("SVO_CERT", "cert.crt")
        monkeypatch.setenv("SVO_KEY", "key.key")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_env(
                config_name="test.json",
                output_dir=tmpdir,
            )

            config = json.loads(output_path.read_text())
            assert config["ssl"]["enabled"] is True

    def test_generate_from_env_http_token(self, monkeypatch):
        """Test generate_from_env with HTTP and token."""
        monkeypatch.setenv("SVO_HOST", "localhost")
        monkeypatch.setenv("SVO_PORT", "8009")
        monkeypatch.setenv("SVO_TOKEN", "token")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = ClientConfigGenerator.generate_from_env(
                config_name="test.json",
                output_dir=tmpdir,
            )

            config = json.loads(output_path.read_text())
            assert config["auth"]["method"] == "api_key"

    def test_save_config_creates_directory(self):
        """Test save_config creates directory if needed."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "subdir"
            output_path = ClientConfigGenerator.save_config(
                config, "test.json", output_dir
            )

            assert output_path.exists()
            assert output_dir.exists()

    def test_load_config_file_not_found(self):
        """Test load_config with non-existent file."""
        with pytest.raises(FileNotFoundError):
            ClientConfigGenerator.load_config("nonexistent.json")

    def test_load_config_invalid_json(self):
        """Test load_config with invalid JSON."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("invalid json {")
            config_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                ClientConfigGenerator.load_config(config_path)
        finally:
            Path(config_path).unlink()

