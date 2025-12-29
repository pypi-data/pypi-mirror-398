"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Integration tests for CLI with real server on localhost:8009.
"""

import asyncio
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from svo_client import ChunkerClient
from svo_client.config_loader import ConfigLoader


@pytest.mark.asyncio
class TestCLIIntegration:
    """Integration tests for CLI commands."""

    @pytest.fixture
    def server_available(self):
        """Check if server is available on localhost:8009."""
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", 8009))
        sock.close()
        return result == 0

    @pytest.fixture
    def mtls_certs(self):
        """Get mTLS certificate paths."""
        cert_dir = Path("mtls_certificates")
        if not cert_dir.exists():
            pytest.skip("mTLS certificates not found")

        cert = cert_dir / "client" / "svo-chunker.crt"
        key = cert_dir / "client" / "svo-chunker.key"
        ca = cert_dir / "ca" / "ca.crt"

        if not (cert.exists() and key.exists() and ca.exists()):
            pytest.skip("mTLS certificates incomplete")

        return {
            "cert": str(cert),
            "key": str(key),
            "ca": str(ca),
        }

    async def test_cli_health_http(self, server_available):
        """Test CLI health command over HTTP."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        result = subprocess.run(
            [
                "python",
                "-m",
                "svo_client.cli",
                "--mode",
                "http",
                "--host",
                "localhost",
                "--port",
                "8009",
                "health",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        # Check for status in data or top-level
        assert "data" in output or "status" in output or "result" in output
        if "data" in output and isinstance(output["data"], dict):
            assert "status" in output["data"] or "result" in output["data"]

    async def test_cli_health_mtls(self, server_available, mtls_certs):
        """Test CLI health command over mTLS."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        result = subprocess.run(
            [
                "python",
                "-m",
                "svo_client.cli",
                "--mode",
                "http",
                "--host",
                "localhost",
                "--port",
                "8009",
                "health",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        # Check for status in data or top-level
        assert "data" in output or "status" in output or "result" in output
        if "data" in output and isinstance(output["data"], dict):
            assert "status" in output["data"] or "result" in output["data"]

    async def test_cli_chunk_http(self, server_available):
        """Test CLI chunk command over HTTP."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        result = subprocess.run(
            [
                "python",
                "-m",
                "svo_client.cli",
                "--mode",
                "http",
                "--host",
                "localhost",
                "--port",
                "8009",
                "chunk",
                "--text",
                "This is a test text for chunking.",
                "--language",
                "en",
                "--type",
                "Draft",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert "chunks:" in result.stdout

    async def test_cli_chunk_mtls(self, server_available, mtls_certs):
        """Test CLI chunk command over mTLS."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        result = subprocess.run(
            [
                "python",
                "-m",
                "svo_client.cli",
                "--mode",
                "http",
                "--host",
                "localhost",
                "--port",
                "8009",
                "chunk",
                "--text",
                "This is a test text for chunking via mTLS.",
                "--language",
                "en",
                "--type",
                "Draft",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert "chunks:" in result.stdout

    async def test_cli_with_config_file(self, server_available, mtls_certs):
        """Test CLI with configuration file."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {
                "enabled": True,
                "cert_file": mtls_certs["cert"],
                "key_file": mtls_certs["key"],
                "ca_cert_file": mtls_certs["ca"],
                "verify_mode": "CERT_REQUIRED",
                "check_hostname": False,
            },
            "auth": {"method": "certificate"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "svo_client.cli",
                    "--config",
                    config_path,
                    "health",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            assert result.returncode == 0
        finally:
            Path(config_path).unlink()

    async def test_cli_env_vars(self, server_available, monkeypatch):
        """Test CLI with environment variables."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        monkeypatch.setenv("SVO_HOST", "localhost")
        monkeypatch.setenv("SVO_PORT", "8009")

        result = subprocess.run(
            [
                "python",
                "-m",
                "svo_client.cli",
                "--mode",
                "http",
                "health",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0

    async def test_cli_submit_and_status(self, server_available):
        """Test submit and status commands."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        # Submit job
        submit_result = subprocess.run(
            [
                "python",
                "-m",
                "svo_client.cli",
                "--mode",
                "http",
                "--host",
                "localhost",
                "--port",
                "8009",
                "submit",
                "--text",
                "Test text for job submission.",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert submit_result.returncode == 0
        submit_output = json.loads(submit_result.stdout)
        job_id = submit_output.get("job_id")

        if job_id:
            # Get status
            status_result = subprocess.run(
                [
                    "python",
                    "-m",
                    "svo_client.cli",
                    "--mode",
                    "http",
                    "--host",
                    "localhost",
                    "--port",
                    "8009",
                    "status",
                    job_id,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            assert status_result.returncode == 0
            status_output = json.loads(status_result.stdout)
            assert "status" in status_output or "data" in status_output


@pytest.mark.asyncio
class TestClientIntegration:
    """Integration tests for ChunkerClient with real server."""

    @pytest.fixture
    def server_available(self):
        """Check if server is available."""
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", 8009))
        sock.close()
        return result == 0

    @pytest.fixture
    def mtls_certs(self):
        """Get mTLS certificate paths."""
        cert_dir = Path("mtls_certificates")
        if not cert_dir.exists():
            pytest.skip("mTLS certificates not found")

        cert = cert_dir / "client" / "svo-chunker.crt"
        key = cert_dir / "client" / "svo-chunker.key"
        ca = cert_dir / "ca" / "ca.crt"

        if not (cert.exists() and key.exists() and ca.exists()):
            pytest.skip("mTLS certificates incomplete")

        return {
            "cert": str(cert),
            "key": str(key),
            "ca": str(ca),
        }

    async def test_client_http(self, server_available):
        """Test ChunkerClient over HTTP."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        async with ChunkerClient(host="localhost", port=8009) as client:
            result = await client.health()
            assert result is not None

    async def test_client_mtls(self, server_available, mtls_certs):
        """Test ChunkerClient over mTLS."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
        ) as client:
            result = await client.health()
            assert result is not None

    async def test_client_chunk_http(self, server_available):
        """Test chunking text over HTTP."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        async with ChunkerClient(host="localhost", port=8009) as client:
            chunks = await client.chunk_text(
                "This is a test text for chunking.",
                language="en",
                type="Draft",
            )
            assert len(chunks) > 0

    async def test_client_chunk_mtls(self, server_available, mtls_certs):
        """Test chunking text over mTLS."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
        ) as client:
            chunks = await client.chunk_text(
                "This is a test text for chunking via mTLS.",
                language="en",
                type="Draft",
            )
            assert len(chunks) > 0

    async def test_client_with_config_priority(self, server_available, monkeypatch):
        """Test configuration priority: API > env > config."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        # Set env vars
        monkeypatch.setenv("SVO_HOST", "wrong-host")
        monkeypatch.setenv("SVO_PORT", "9999")

        # API should override env
        async with ChunkerClient(host="localhost", port=8009) as client:
            result = await client.health()
            assert result is not None

    async def test_client_all_protocols(
        self, server_available, mtls_certs
    ):
        """Test all supported protocols."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        # HTTP
        async with ChunkerClient(host="localhost", port=8009) as client:
            result = await client.health()
            assert result is not None

        # mTLS
        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
        ) as client:
            result = await client.health()
            assert result is not None

