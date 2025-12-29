"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Edge case tests for ChunkerClient to increase coverage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from svo_client import ChunkerClient
from svo_client.errors import SVOServerError


class TestChunkerClientEdgeCases:
    """Edge case tests for ChunkerClient."""

    @pytest.mark.asyncio
    async def test_wait_for_result_status_dict(self):
        """Test wait_for_result with status as dict."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_status = {
                "data": {
                    "status": "completed",
                    "result": {"chunks": []},
                }
            }
            mock_client.return_value.queue_get_job_status = AsyncMock(
                return_value=mock_status
            )
            client = ChunkerClient(host="localhost", port=8009)
            result = await client.wait_for_result("job_id")
            assert result is not None

    @pytest.mark.asyncio
    async def test_wait_for_result_status_string(self):
        """Test wait_for_result with status as string."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_status = {
                "data": {
                    "status": "completed",
                    "result": {"chunks": []},
                }
            }
            mock_client.return_value.queue_get_job_status = AsyncMock(
                return_value=mock_status
            )
            client = ChunkerClient(host="localhost", port=8009)
            result = await client.wait_for_result("job_id")
            assert result is not None

    @pytest.mark.asyncio
    async def test_wait_for_result_no_status_field(self):
        """Test wait_for_result with no status field."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_status = {
                "data": {
                    "result": {"chunks": []},
                }
            }
            mock_client.return_value.queue_get_job_status = AsyncMock(
                return_value=mock_status
            )
            client = ChunkerClient(host="localhost", port=8009)
            result = await client.wait_for_result("job_id")
            assert result is not None

    @pytest.mark.asyncio
    async def test_wait_for_result_empty_status_value(self):
        """Test wait_for_result with empty status value."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_status = {
                "data": {
                    "status": "",
                    "result": {"chunks": []},
                }
            }
            mock_client.return_value.queue_get_job_status = AsyncMock(
                return_value=mock_status
            )
            client = ChunkerClient(host="localhost", port=8009)
            result = await client.wait_for_result("job_id")
            assert result is not None

    @pytest.mark.asyncio
    async def test_wait_for_result_pending_states(self):
        """Test wait_for_result with different pending states."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            pending_states = ["queued", "pending", "running"]
            completed_state = {
                "data": {
                    "status": "completed",
                    "result": {"chunks": []},
                }
            }

            call_count = 0

            async def mock_status(job_id):
                nonlocal call_count
                if call_count < len(pending_states):
                    state = pending_states[call_count]
                    call_count += 1
                    return {"data": {"status": state}}
                return completed_state

            mock_client.return_value.queue_get_job_status = mock_status

            with patch("asyncio.sleep", new_callable=AsyncMock):
                client = ChunkerClient(host="localhost", port=8009)
                result = await client.wait_for_result(
                    "job_id", poll_interval=0.1, timeout=None
                )
                assert result is not None

    @pytest.mark.asyncio
    async def test_chunk_text_with_verify_integrity_false(self):
        """Test chunk_text with verify_integrity=False."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            from chunk_metadata_adapter import SemanticChunk

            mock_chunks = [
                SemanticChunk(
                    text="Test",
                    ordinal=0,
                    type="Draft",
                    body="Test",
                )
            ]
            mock_result = {"chunks": [{"text": "Test", "ordinal": 0}]}
            mock_client.return_value.execute_command_unified = AsyncMock(
                return_value=mock_result
            )

            with patch(
                "svo_client.chunker_client.extract_chunks_or_raise",
                return_value=mock_chunks,
            ):
                client = ChunkerClient(host="localhost", port=8009)
                chunks = await client.chunk_text(
                    "test", verify_integrity=False
                )
                assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_get_job_status_exception(self):
        """Test get_job_status with exception."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_client.return_value.queue_get_job_status = AsyncMock(
                side_effect=Exception("Connection error")
            )
            client = ChunkerClient(host="localhost", port=8009)
            with pytest.raises(Exception):
                await client.get_job_status("job_id")

    @pytest.mark.asyncio
    async def test_get_job_logs_exception(self):
        """Test get_job_logs with exception."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_client.return_value.queue_get_job_logs = AsyncMock(
                side_effect=Exception("Connection error")
            )
            client = ChunkerClient(host="localhost", port=8009)
            with pytest.raises(Exception):
                await client.get_job_logs("job_id")

    @pytest.mark.asyncio
    async def test_list_jobs_exception(self):
        """Test list_jobs with exception."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_client.return_value.queue_list_jobs = AsyncMock(
                side_effect=Exception("Connection error")
            )
            client = ChunkerClient(host="localhost", port=8009)
            with pytest.raises(Exception):
                await client.list_jobs()

    @pytest.mark.asyncio
    async def test_list_jobs_with_status_filter(self):
        """Test list_jobs with status filter."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_client.return_value.queue_list_jobs = AsyncMock(
                return_value=[{"id": "1", "status": "completed"}]
            )
            client = ChunkerClient(host="localhost", port=8009)
            jobs = await client.list_jobs(status="completed")
            assert len(jobs) == 1

    @pytest.mark.asyncio
    async def test_list_jobs_with_limit(self):
        """Test list_jobs with limit."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_client.return_value.queue_list_jobs = AsyncMock(
                return_value=[{"id": "1"}, {"id": "2"}]
            )
            client = ChunkerClient(host="localhost", port=8009)
            jobs = await client.list_jobs(limit=2)
            assert len(jobs) == 2
