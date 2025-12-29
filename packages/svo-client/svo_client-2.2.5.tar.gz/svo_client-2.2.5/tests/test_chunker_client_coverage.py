"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Additional tests to increase coverage for ChunkerClient.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from svo_client import ChunkerClient
from svo_client.errors import (
    SVOChunkingIntegrityError,
    SVOServerError,
    SVOTimeoutError,
)


class TestChunkerClientCoverage:
    """Tests to increase ChunkerClient coverage."""

    def test_init_with_config(self):
        """Test initialization with pre-built config."""
        config = {
            "server": {"host": "localhost", "port": 8009},
            "ssl": {"enabled": False},
            "auth": {"method": "none"},
        }

        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_client.return_value = AsyncMock()
            client = ChunkerClient(config=config)
            assert client.host == "localhost"
            assert client.port == 8009

    def test_init_with_timeout_none(self):
        """Test initialization with timeout=None."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_transport = MagicMock()
            mock_client.return_value = mock_transport
            client = ChunkerClient(host="localhost", port=8009, timeout=None)
            # Timeout should be None (no timeout)
            assert client.timeout is None

    def test_init_with_timeout_value(self):
        """Test initialization with timeout value."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_transport = MagicMock()
            mock_client.return_value = mock_transport
            client = ChunkerClient(host="localhost", port=8009, timeout=60.0)
            assert client.timeout == 60.0

    @pytest.mark.asyncio
    async def test_close(self):
        """Test close method."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_close = AsyncMock()
            mock_client.return_value.close = mock_close
            client = ChunkerClient(host="localhost", port=8009)
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_close = AsyncMock()
            mock_client.return_value.close = mock_close
            async with ChunkerClient(host="localhost", port=8009) as client:
                assert client is not None
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_openapi_schema(self):
        """Test get_openapi_schema method."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_schema = {"openapi": "3.0.0"}
            mock_client.return_value.get_openapi_schema = AsyncMock(
                return_value=mock_schema
            )
            client = ChunkerClient(host="localhost", port=8009)
            schema = await client.get_openapi_schema()
            assert schema == mock_schema

    @pytest.mark.asyncio
    async def test_submit_chunk_job_no_job_id(self):
        """Test submit_chunk_job when no job_id is returned."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_result = {"result": {}}
            mock_client.return_value.execute_command_unified = AsyncMock(
                return_value=mock_result
            )
            client = ChunkerClient(host="localhost", port=8009)
            with pytest.raises(SVOServerError, match="no_job_id"):
                await client.submit_chunk_job("test text")

    @pytest.mark.asyncio
    async def test_wait_for_result_timeout(self):
        """Test wait_for_result with timeout."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            import time

            mock_status = {"status": "running"}
            mock_client.return_value.queue_get_job_status = AsyncMock(
                return_value=mock_status
            )
            client = ChunkerClient(host="localhost", port=8009)
            with patch("time.monotonic", side_effect=[0, 31]):
                with pytest.raises(SVOTimeoutError):
                    await client.wait_for_result(
                        "job_id", poll_interval=1.0, timeout=30.0
                    )

    @pytest.mark.asyncio
    async def test_wait_for_result_failed(self):
        """Test wait_for_result with failed job."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_status = {
                "data": {
                    "success": False,
                    "error": {"code": "test_error", "message": "Test"},
                }
            }
            mock_client.return_value.queue_get_job_status = AsyncMock(
                return_value=mock_status
            )
            client = ChunkerClient(host="localhost", port=8009)
            with pytest.raises(SVOServerError, match="test_error"):
                await client.wait_for_result("job_id")

    @pytest.mark.asyncio
    async def test_wait_for_result_integrity_error(self):
        """Test wait_for_result with integrity error."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_status = {
                "data": {
                    "success": False,
                    "error": {
                        "code": "integrity_error",
                        "message": "Integrity check failed",
                        "data": {
                            "error": "ChunkingIntegrityError",
                            "original_text_length": 100,
                            "reconstructed_text_length": 95,
                            "chunk_count": 5,
                            "integrity_error": "Mismatch",
                        },
                    },
                }
            }
            mock_client.return_value.queue_get_job_status = AsyncMock(
                return_value=mock_status
            )
            client = ChunkerClient(host="localhost", port=8009)
            with pytest.raises(SVOChunkingIntegrityError):
                await client.wait_for_result("job_id")

    @pytest.mark.asyncio
    async def test_chunk_text_integrity_exception(self):
        """Test chunk_text with integrity exception."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            error = RuntimeError("Integrity check failed")
            error.data = {
                "error": "ChunkingIntegrityError",
                "original_text_length": 100,
                "reconstructed_text_length": 95,
            }
            mock_client.return_value.execute_command_unified = AsyncMock(
                side_effect=error
            )
            client = ChunkerClient(host="localhost", port=8009)
            with pytest.raises(SVOChunkingIntegrityError):
                await client.chunk_text("test text", verify_integrity=True)

    @pytest.mark.asyncio
    async def test_list_jobs_empty(self):
        """Test list_jobs with empty result."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_client.return_value.queue_list_jobs = AsyncMock(
                return_value={}
            )
            client = ChunkerClient(host="localhost", port=8009)
            jobs = await client.list_jobs()
            assert jobs == []

    @pytest.mark.asyncio
    async def test_list_jobs_with_data(self):
        """Test list_jobs with data in response."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_client.return_value.queue_list_jobs = AsyncMock(
                return_value={"jobs": [{"id": "1"}, {"id": "2"}]}
            )
            client = ChunkerClient(host="localhost", port=8009)
            jobs = await client.list_jobs()
            assert len(jobs) == 2

    @pytest.mark.asyncio
    async def test_list_jobs_direct_list(self):
        """Test list_jobs with direct list response."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_client.return_value.queue_list_jobs = AsyncMock(
                return_value=[{"id": "1"}, {"id": "2"}]
            )
            client = ChunkerClient(host="localhost", port=8009)
            jobs = await client.list_jobs()
            assert len(jobs) == 2

    def test_reconstruct_text(self):
        """Test reconstruct_text method."""
        from chunk_metadata_adapter import SemanticChunk

        chunks = [
            SemanticChunk(
                text="Hello ",
                ordinal=0,
                type="Draft",
                body="Hello ",
            ),
            SemanticChunk(
                text="world",
                ordinal=1,
                type="Draft",
                body="world",
            ),
        ]

        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            client = ChunkerClient(host="localhost", port=8009)
            result = client.reconstruct_text(chunks)
            assert result == "Hello world"

    def test_verify_text_integrity(self):
        """Test verify_text_integrity method."""
        from chunk_metadata_adapter import SemanticChunk

        chunks = [
            SemanticChunk(
                text="Hello ",
                ordinal=0,
                type="Draft",
                body="Hello ",
            ),
            SemanticChunk(
                text="world",
                ordinal=1,
                type="Draft",
                body="world",
            ),
        ]

        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            client = ChunkerClient(host="localhost", port=8009)
            result = client.verify_text_integrity(chunks, "Hello world")
            assert result is True
