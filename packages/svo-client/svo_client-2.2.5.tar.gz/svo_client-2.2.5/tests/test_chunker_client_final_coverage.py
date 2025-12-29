"""
Final coverage tests for ChunkerClient to reach 90%+.
"""

import asyncio
import uuid
from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest

from svo_client import ChunkerClient, SVOServerError


def make_valid_chunk_dict(text: str, ordinal: int) -> Dict[str, Any]:
    """Build minimal valid chunk dict."""
    return {
        "uuid": str(uuid.uuid4()),
        "type": "DocBlock",
        "text": text,
        "body": text,
        "summary": "summary",
        "sha256": "a" * 64,
        "language": "en",
        "created_at": "2024-01-01T00:00:00+00:00",
        "status": "new",
        "start": 0,
        "end": len(text),
        "metrics": {},
        "links": [],
        "tags": [],
        "embedding": [1.0],
        "role": "user",
        "project": "proj",
        "task_id": str(uuid.uuid4()),
        "subtask_id": str(uuid.uuid4()),
        "unit_id": str(uuid.uuid4()),
        "source_id": str(uuid.uuid4()),
        "source_path": "/path",
        "source_lines": [1, 2],
        "ordinal": ordinal,
        "chunking_version": "1.0",
    }


@pytest.mark.asyncio
async def test_get_openapi_schema_error():
    """Test get_openapi_schema with error."""
    mock_client = AsyncMock()
    mock_client.get_openapi_schema = AsyncMock(side_effect=ConnectionError("Error"))
    
    client = ChunkerClient()
    client._client = mock_client
    
    from svo_client import SVOConnectionError
    with pytest.raises(SVOConnectionError):
        await client.get_openapi_schema()
    
    await client.close()


@pytest.mark.asyncio
async def test_submit_chunk_job_error():
    """Test submit_chunk_job with error."""
    mock_client = AsyncMock()
    mock_client.execute_command_unified = AsyncMock(side_effect=RuntimeError("Error"))
    
    client = ChunkerClient()
    client._client = mock_client
    
    from svo_client import SVOJSONRPCError
    with pytest.raises(SVOJSONRPCError):
        await client.submit_chunk_job("test")
    
    await client.close()


@pytest.mark.asyncio
async def test_get_job_status_error():
    """Test get_job_status with error."""
    mock_client = AsyncMock()
    mock_client.queue_get_job_status = AsyncMock(side_effect=ConnectionError("Error"))
    
    client = ChunkerClient()
    client._client = mock_client
    
    from svo_client import SVOConnectionError
    with pytest.raises(SVOConnectionError):
        await client.get_job_status("test-job")
    
    await client.close()


@pytest.mark.asyncio
async def test_get_job_logs_error():
    """Test get_job_logs with error."""
    mock_client = AsyncMock()
    mock_client.queue_get_job_logs = AsyncMock(side_effect=ConnectionError("Error"))
    
    client = ChunkerClient()
    client._client = mock_client
    
    from svo_client import SVOConnectionError
    with pytest.raises(SVOConnectionError):
        await client.get_job_logs("test-job")
    
    await client.close()


@pytest.mark.asyncio
async def test_wait_for_result_exception():
    """Test wait_for_result with exception during status check."""
    mock_client = AsyncMock()
    mock_client.queue_get_job_status = AsyncMock(side_effect=ConnectionError("Error"))
    
    client = ChunkerClient()
    client._client = mock_client
    
    from svo_client import SVOConnectionError
    with pytest.raises(SVOConnectionError):
        await client.wait_for_result("test-job", timeout=10.0)
    
    await client.close()


@pytest.mark.asyncio
async def test_wait_for_result_status_in_dict():
    """Test wait_for_result when status is in top-level dict."""
    mock_client = AsyncMock()
    mock_client.queue_get_job_status = AsyncMock(
        return_value={"status": "completed", "result": {"chunks": []}}
    )
    
    client = ChunkerClient()
    client._client = mock_client
    
    result = await client.wait_for_result("test-job", timeout=10.0)
    assert isinstance(result, dict)
    
    await client.close()

