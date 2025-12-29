"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests to increase ConfigTools coverage.
"""

import pytest

from svo_client.config_tools import ConfigGenerator, ConfigValidator


class TestConfigToolsCoverage:
    """Tests to increase ConfigTools coverage."""

    def test_config_generator_base(self):
        """Test ConfigGenerator._base method."""
        cfg = ConfigGenerator._base("localhost", 8009)
        assert cfg["server"]["host"] == "localhost"
        assert cfg["server"]["port"] == 8009

    def test_config_generator_base_with_timeout(self):
        """Test ConfigGenerator._base with timeout."""
        cfg = ConfigGenerator._base("localhost", 8009, timeout=60.0)
        assert cfg["timeout"] == 60.0

    def test_config_generator_ssl(self):
        """Test ConfigGenerator._ssl method."""
        cfg = ConfigGenerator._ssl(
            enabled=True,
            cert="cert.crt",
            key="key.key",
            ca="ca.crt",
            check_hostname=True,
            verify_mode="CERT_REQUIRED",
        )
        assert cfg["enabled"] is True
        assert cfg["cert_file"] == "cert.crt"
        assert cfg["key_file"] == "key.key"
        assert cfg["ca_cert_file"] == "ca.crt"
        assert cfg["check_hostname"] is True
        assert cfg["verify_mode"] == "CERT_REQUIRED"

    def test_config_generator_ssl_disabled(self):
        """Test ConfigGenerator._ssl with disabled SSL."""
        cfg = ConfigGenerator._ssl(enabled=False)
        assert cfg["enabled"] is False

    def test_config_generator_auth_none(self):
        """Test ConfigGenerator._auth_none method."""
        cfg = ConfigGenerator._auth_none()
        assert cfg["method"] == "none"

    def test_config_generator_auth_api_key(self):
        """Test ConfigGenerator._auth_api_key method."""
        cfg = ConfigGenerator._auth_api_key("token", "X-API-Key", ["admin"])
        assert cfg["method"] == "api_key"
        assert cfg["header"] == "X-API-Key"
        assert cfg["api_keys"]["default"] == "token"
        assert cfg["roles"] == ["admin"]

    def test_config_generator_auth_api_key_no_roles(self):
        """Test ConfigGenerator._auth_api_key without roles."""
        cfg = ConfigGenerator._auth_api_key("token", "X-API-Key", None)
        assert cfg["method"] == "api_key"
        assert "roles" not in cfg or cfg.get("roles") is None

    def test_config_generator_auth_cert(self):
        """Test ConfigGenerator._auth_cert method."""
        cfg = ConfigGenerator._auth_cert(["admin", "user"])
        assert cfg["method"] == "certificate"
        assert cfg["roles"] == ["admin", "user"]

    def test_config_generator_auth_cert_no_roles(self):
        """Test ConfigGenerator._auth_cert without roles."""
        cfg = ConfigGenerator._auth_cert(None)
        assert cfg["method"] == "certificate"
        assert "roles" not in cfg or cfg.get("roles") is None

    def test_config_generator_http(self):
        """Test ConfigGenerator.http method."""
        cfg = ConfigGenerator.http("localhost", 8009)
        assert cfg["server"]["host"] == "localhost"
        assert cfg["server"]["port"] == 8009
        assert cfg["ssl"]["enabled"] is False
        assert cfg["auth"]["method"] == "none"

    def test_config_generator_http_token(self):
        """Test ConfigGenerator.http_token method."""
        cfg = ConfigGenerator.http_token(
            "localhost", 8009, "token", "X-API-Key", ["admin"]
        )
        assert cfg["server"]["host"] == "localhost"
        assert cfg["ssl"]["enabled"] is False
        assert cfg["auth"]["method"] == "api_key"
        assert cfg["auth"]["api_keys"]["default"] == "token"

    def test_config_generator_https(self):
        """Test ConfigGenerator.https method."""
        cfg = ConfigGenerator.https("localhost", 8009, check_hostname=True)
        assert cfg["ssl"]["enabled"] is True
        assert cfg["ssl"]["check_hostname"] is True
        assert cfg["auth"]["method"] == "none"

    def test_config_generator_https_token(self):
        """Test ConfigGenerator.https_token method."""
        cfg = ConfigGenerator.https_token(
            "localhost",
            8009,
            "token",
            "Authorization",
            ["admin"],
            check_hostname=True,
        )
        assert cfg["ssl"]["enabled"] is True
        assert cfg["auth"]["method"] == "api_key"
        assert cfg["auth"]["header"] == "Authorization"

    def test_config_generator_mtls(self):
        """Test ConfigGenerator.mtls method."""
        cfg = ConfigGenerator.mtls(
            "localhost",
            8009,
            "cert.crt",
            "key.key",
            "ca.crt",
            ["admin"],
            check_hostname=False,
        )
        assert cfg["ssl"]["enabled"] is True
        assert cfg["ssl"]["verify_mode"] == "CERT_REQUIRED"
        assert cfg["auth"]["method"] == "certificate"

    def test_config_validator_invalid_dict(self):
        """Test ConfigValidator with invalid dict."""
        with pytest.raises(ValueError, match="must be a dict"):
            ConfigValidator.validate("not a dict")

    def test_config_validator_invalid_server(self):
        """Test ConfigValidator with invalid server section."""
        with pytest.raises(ValueError, match="server must be a dict"):
            ConfigValidator.validate({"server": "not a dict"})

    def test_config_validator_invalid_ssl(self):
        """Test ConfigValidator with invalid ssl section."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": "not a dict",
            "auth": {"method": "none"},
        }
        with pytest.raises(ValueError, match="ssl must be a dict"):
            ConfigValidator.validate(config)

    def test_config_validator_invalid_auth(self):
        """Test ConfigValidator with invalid auth section."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {"enabled": False},
            "auth": "not a dict",
        }
        with pytest.raises(ValueError, match="auth must be a dict"):
            ConfigValidator.validate(config)

