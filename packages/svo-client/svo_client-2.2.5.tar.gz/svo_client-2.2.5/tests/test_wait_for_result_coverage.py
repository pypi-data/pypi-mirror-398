"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests for wait_for_result edge cases to increase coverage.
"""

import pytest
from unittest.mock import AsyncMock, patch

from svo_client import ChunkerClient
from svo_client.errors import SVOChunkingIntegrityError, SVOServerError


class TestWaitForResultCoverage:
    """Tests for wait_for_result edge cases."""

    @pytest.mark.asyncio
    async def test_wait_for_result_status_in_dict(self):
        """Test wait_for_result with status in top-level dict."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_status = {
                "status": "completed",
                "data": {"result": {"chunks": []}},
            }
            mock_client.return_value.queue_get_job_status = AsyncMock(
                return_value=mock_status
            )
            client = ChunkerClient(host="localhost", port=8009)
            result = await client.wait_for_result("job_id")
            assert result is not None

    @pytest.mark.asyncio
    async def test_wait_for_result_state_field(self):
        """Test wait_for_result with state field instead of status."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_status = {
                "data": {
                    "state": "completed",
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
    async def test_wait_for_result_non_dict_status(self):
        """Test wait_for_result with non-dict status."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_status = "completed"
            mock_client.return_value.queue_get_job_status = AsyncMock(
                return_value=mock_status
            )
            client = ChunkerClient(host="localhost", port=8009)
            result = await client.wait_for_result("job_id")
            assert result is not None

    @pytest.mark.asyncio
    async def test_wait_for_result_error_not_dict(self):
        """Test wait_for_result with error not a dict."""
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
            with pytest.raises(SVOServerError):
                await client.wait_for_result("job_id")

    @pytest.mark.asyncio
    async def test_wait_for_result_error_data_not_dict(self):
        """Test wait_for_result with error.data not a dict."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_status = {
                "data": {
                    "success": False,
                    "error": {
                        "code": "test_error",
                        "message": "Test",
                        "data": "not a dict",
                    },
                }
            }
            mock_client.return_value.queue_get_job_status = AsyncMock(
                return_value=mock_status
            )
            client = ChunkerClient(host="localhost", port=8009)
            with pytest.raises(SVOServerError):
                await client.wait_for_result("job_id")

    @pytest.mark.asyncio
    async def test_wait_for_result_no_result_field(self):
        """Test wait_for_result with no result field."""
        with patch(
            "svo_client.chunker_client.JsonRpcClient"
        ) as mock_client:
            mock_status = {
                "data": {
                    "status": "completed",
                    "chunks": [],
                }
            }
            mock_client.return_value.queue_get_job_status = AsyncMock(
                return_value=mock_status
            )
            client = ChunkerClient(host="localhost", port=8009)
            result = await client.wait_for_result("job_id")
            assert result is not None

