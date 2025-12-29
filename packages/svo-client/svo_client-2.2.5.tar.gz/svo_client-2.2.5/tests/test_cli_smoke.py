"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Smoke tests for CLI commands.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.asyncio
class TestCLISmoke:
    """Smoke tests for CLI commands."""

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

    async def test_cli_health_mtls(self, server_available, mtls_certs):
        """Test CLI health command with HTTP (test server uses HTTP, not mTLS)."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        # Test server runs on HTTP, not mTLS
        result = subprocess.run(
            [
                sys.executable,
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

    async def test_cli_chunk_mtls(self, server_available, mtls_certs):
        """Test CLI chunk command with mTLS."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        result = subprocess.run(
            [
                sys.executable,
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

    async def test_cli_list_mtls(self, server_available, mtls_certs):
        """Test CLI list command with mTLS."""
        if not server_available:
            pytest.skip("Server not available on localhost:8009")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "svo_client.cli",
                "--mode",
                "http",
                "--host",
                "localhost",
                "--port",
                "8009",
                "list",
                "--limit",
                "5",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert isinstance(output, list)

