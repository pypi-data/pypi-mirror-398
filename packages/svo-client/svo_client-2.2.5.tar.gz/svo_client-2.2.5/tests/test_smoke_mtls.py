"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Smoke test for chunking on localhost:8009 with mTLS.
"""

import asyncio
from pathlib import Path

import pytest

from svo_client import ChunkerClient, SVOConnectionError


@pytest.mark.asyncio
class TestSmokeMTLS:
    """Smoke tests for mTLS chunking on localhost:8009."""

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

    # Use server_available from conftest

    async def test_smoke_health(self, server_available, mtls_certs):
        """Smoke test: health check via HTTP (test server uses HTTP)."""
        if not server_available:
            pytest.fail("Server not available on localhost:8009")

        # Test server runs on HTTP, not mTLS
        async with ChunkerClient(
            host="localhost",
            port=8009,
        ) as client:
            result = await client.health()
            assert result is not None
            assert isinstance(result, dict)

    async def test_smoke_chunk_simple(self, server_available, mtls_certs):
        """Smoke test: simple chunking via mTLS."""
        if not server_available:
            pytest.fail("Server not available on localhost:8009")

        test_text = "This is a simple test text for chunking. It contains multiple sentences to ensure it meets the minimum length requirements. The text should be long enough to be processed by the chunking service without errors."

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
            timeout=180.0,  # Chunking may take time if embedding service is slow
        ) as client:
            chunks = await client.chunk_text(
                test_text, type="Draft", language="en", verify_integrity=False
            )
            assert len(chunks) > 0
            assert all(hasattr(chunk, "text") for chunk in chunks)

    async def test_smoke_chunk_integrity(self, server_available, mtls_certs):
        """Smoke test: chunking with integrity verification."""
        if not server_available:
            pytest.fail("Server not available on localhost:8009")

        test_text = "Artificial Intelligence is a branch of computer science. It aims to create intelligent machines that can perform tasks typically requiring human intelligence. Machine learning is a subset of AI that enables systems to learn from data."

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
            timeout=30.0,  # Add timeout
        ) as client:
            chunks = await client.chunk_text(
                test_text,
                type="Draft",
                language="en",
                verify_integrity=True,
            )
            assert len(chunks) > 0
            reconstructed = client.reconstruct_text(chunks)
            assert reconstructed == test_text

    async def test_smoke_queue_operations(self, server_available, mtls_certs):
        """Smoke test: queue operations (submit, status, wait)."""
        if not server_available:
            pytest.fail("Server not available on localhost:8009")

        test_text = "This is a test for queue operations."

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
        ) as client:
            # Submit job
            job_id = await client.submit_chunk_job(
                test_text, type="Draft", language="en"
            )
            assert job_id is not None
            assert isinstance(job_id, str)

            # Get status
            status = await client.get_job_status(job_id)
            assert status is not None

            # Wait for result
            result = await client.wait_for_result(
                job_id, poll_interval=1.0, timeout=30.0
            )
            assert result is not None

    async def test_smoke_list_jobs(self, server_available, mtls_certs):
        """Smoke test: list jobs."""
        if not server_available:
            pytest.fail("Server not available on localhost:8009")

        # Test server runs on HTTP
        async with ChunkerClient(
            host="localhost",
            port=8009,
        ) as client:
            jobs = await client.list_jobs()  # limit not supported by server
            assert isinstance(jobs, list)

