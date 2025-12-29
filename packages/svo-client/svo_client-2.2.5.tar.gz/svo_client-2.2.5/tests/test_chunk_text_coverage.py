"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests for chunk_text method to increase coverage.
"""

import pytest
from unittest.mock import AsyncMock, patch

from svo_client import ChunkerClient
from svo_client.errors import SVOChunkingIntegrityError


class TestChunkTextCoverage:
    """Tests for chunk_text method edge cases."""

    @pytest.mark.asyncio
    async def test_chunk_text_runtime_error_no_integrity(self):
        """Test chunk_text with RuntimeError without integrity."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            error = RuntimeError("Some other error")
            mock_client.return_value.execute_command_unified = AsyncMock(
                side_effect=error
            )
            client = ChunkerClient(host="localhost", port=8009)
            with pytest.raises(Exception):
                await client.chunk_text("test text")

    @pytest.mark.asyncio
    async def test_chunk_text_runtime_error_no_data(self):
        """Test chunk_text with RuntimeError without data attribute."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            error = RuntimeError("Integrity check failed")
            # No data attribute
            mock_client.return_value.execute_command_unified = AsyncMock(
                side_effect=error
            )
            client = ChunkerClient(host="localhost", port=8009)
            with pytest.raises(Exception):
                await client.chunk_text("test text")

    @pytest.mark.asyncio
    async def test_chunk_text_runtime_error_data_not_dict(self):
        """Test chunk_text with RuntimeError with data not a dict."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            error = RuntimeError("Integrity check failed")
            error.data = "not a dict"
            mock_client.return_value.execute_command_unified = AsyncMock(
                side_effect=error
            )
            client = ChunkerClient(host="localhost", port=8009)
            with pytest.raises(Exception):
                await client.chunk_text("test text")

    @pytest.mark.asyncio
    async def test_chunk_text_runtime_error_wrong_error_type(self):
        """Test chunk_text with RuntimeError with wrong error type."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            error = RuntimeError("Integrity check failed")
            error.data = {"error": "DifferentError"}
            mock_client.return_value.execute_command_unified = AsyncMock(
                side_effect=error
            )
            client = ChunkerClient(host="localhost", port=8009)
            with pytest.raises(Exception):
                await client.chunk_text("test text")

    @pytest.mark.asyncio
    async def test_chunk_text_with_verify_integrity_true(self):
        """Test chunk_text with verify_integrity=True."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            from chunk_metadata_adapter import SemanticChunk

            mock_chunks = [
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
            mock_result = {
                "chunks": [
                    {"text": "Hello ", "ordinal": 0},
                    {"text": "world", "ordinal": 1},
                ]
            }
            mock_client.return_value.execute_command_unified = AsyncMock(
                return_value=mock_result
            )

            with patch(
                "svo_client.chunker_client.extract_chunks_or_raise",
                return_value=mock_chunks,
            ):
                with patch(
                    "svo_client.chunker_client.verify_text_integrity"
                ) as mock_verify:
                    mock_verify.return_value = True
                    client = ChunkerClient(host="localhost", port=8009)
                    chunks = await client.chunk_text(
                        "Hello world", verify_integrity=True
                    )
                    assert len(chunks) == 2
                    mock_verify.assert_called_once()

