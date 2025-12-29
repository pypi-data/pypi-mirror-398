"""
Edge case tests for result_parser to achieve 90%+ coverage.
"""

import uuid

import pytest

from svo_client.errors import SVOServerError
from svo_client.result_parser import (
    extract_chunks_or_raise,
    extract_job_id,
    unwrap_result,
)


def make_valid_chunk_dict(text: str, ordinal: int) -> dict:
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


def test_extract_job_id_jobId():
    """Test extracting job ID from jobId field."""
    payload = {"jobId": "test-job-789"}
    assert extract_job_id(payload) == "test-job-789"


def test_unwrap_result_with_raw_status():
    """Test unwrapping result with raw_status containing completed job."""
    payload = {
        "raw_status": {
            "success": True,
            "data": {
                "status": "completed",
                "result": {
                    "chunks": [make_valid_chunk_dict("test", 0)]
                }
            }
        }
    }
    result = unwrap_result(payload)
    assert "chunks" in result


def test_unwrap_result_triple_nested():
    """Test unwrapping triple-nested result structure."""
    payload = {
        "result": {
            "result": {
                "result": {
                    "chunks": [make_valid_chunk_dict("test", 0)]
                }
            }
        }
    }
    result = unwrap_result(payload)
    assert "chunks" in result


def test_unwrap_result_nested_error():
    """Test unwrapping nested error structure."""
    payload = {
        "result": {
            "result": {
                "success": False,
                "error": {"code": -32603, "message": "Error"}
            }
        }
    }
    result = unwrap_result(payload)
    assert result["success"] is False


def test_extract_chunks_or_raise_data_chunks():
    """Test extracting chunks from result['data']['chunks']."""
    result = {
        "data": {
            "chunks": [make_valid_chunk_dict("test", 0)]
        }
    }
    chunks = extract_chunks_or_raise(result)
    assert len(chunks) == 1


def test_extract_chunks_or_raise_data_result_chunks():
    """Test extracting chunks from result['data']['result']['chunks']."""
    result = {
        "data": {
            "result": {
                "chunks": [make_valid_chunk_dict("test", 0)]
            }
        }
    }
    chunks = extract_chunks_or_raise(result)
    assert len(chunks) == 1


def test_extract_chunks_or_raise_deeply_nested():
    """Test extracting chunks from deeply nested structure."""
    result = {
        "data": {
            "result": {
                "result": {
                    "data": {
                        "chunks": [make_valid_chunk_dict("test", 0)]
                    }
                }
            }
        }
    }
    chunks = extract_chunks_or_raise(result)
    assert len(chunks) == 1


def test_extract_chunks_or_raise_with_chunk_error():
    """Test extracting chunks when chunk contains error."""
    result = {
        "chunks": [
            {
                "error": {
                    "code": "chunk_error",
                    "message": "Chunk processing failed"
                }
            }
        ]
    }
    with pytest.raises(SVOServerError) as exc_info:
        extract_chunks_or_raise(result)
    assert exc_info.value.code == "chunk_error"


def test_unwrap_result_invalid_type():
    """Test unwrapping result with invalid type."""
    payload = "not a dict"
    with pytest.raises(SVOServerError) as exc_info:
        unwrap_result(payload)
    assert exc_info.value.code == "invalid_result"

