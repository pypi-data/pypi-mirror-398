"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests for _build_config function to increase CLI coverage.
"""

import argparse
import tempfile
from pathlib import Path

import pytest

from svo_client.cli import _build_config


class TestCLIBuildConfig:
    """Tests for _build_config function."""

    def test_build_config_all_modes(self):
        """Test _build_config with all supported modes."""
        modes = [
            "http",
            "http_token",
            "http_token_roles",
            "https",
            "https_token",
            "https_token_roles",
            "mtls",
            "mtls_token",
            "mtls_roles",
        ]

        for mode in modes:
            # Create Args object for this mode
            args = argparse.Namespace()
            args.mode = mode
            args.host = "localhost"
            args.port = 8009
            args.token = "test-token" if "token" in mode else None
            args.token_header = "X-API-Key"
            args.roles = "admin,user" if "roles" in mode else None
            args.cert = "cert.crt" if "mtls" in mode else None
            args.key = "key.key" if "mtls" in mode else None
            args.ca = "ca.crt" if "mtls" in mode else None
            args.check_hostname = False
            args.config = None

            if "mtls" in mode and not (args.cert and args.key and args.ca):
                with pytest.raises(SystemExit):
                    _build_config(args)
            elif "token" in mode and not args.token:
                with pytest.raises(SystemExit):
                    _build_config(args)
            else:
                config = _build_config(args)
                assert config is not None
                assert config["server"]["host"] == "localhost"

    def test_build_config_with_config_file(self):
        """Test _build_config with config file."""
        config = {
            "server": {"host": "file-host", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            import json

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

    def test_build_config_unsupported_mode(self):
        """Test _build_config with unsupported mode."""
        class Args:
            mode = "unsupported"
            host = "localhost"
            port = 8009
            token = None
            token_header = "X-API-Key"
            roles = None
            cert = None
            key = None
            ca = None
            check_hostname = False
            config = None

        with pytest.raises(SystemExit, match="Unsupported mode"):
            _build_config(Args())

