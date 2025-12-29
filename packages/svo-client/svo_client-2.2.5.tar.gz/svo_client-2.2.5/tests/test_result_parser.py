"""
Tests for result_parser module.
"""

import uuid

import pytest
from chunk_metadata_adapter import ChunkMetadataBuilder, SemanticChunk

from svo_client.errors import SVOChunkingIntegrityError, SVOServerError
from svo_client.result_parser import (
    extract_chunks_or_raise,
    extract_job_id,
    parse_chunk_static,
    unwrap_result,
)


def test_extract_job_id_direct():
    """Test extracting job ID from direct field."""
    payload = {"job_id": "test-job-123"}
    assert extract_job_id(payload) == "test-job-123"


def test_extract_job_id_nested():
    """Test extracting job ID from nested result."""
    payload = {"result": {"job_id": "test-job-456"}}
    assert extract_job_id(payload) == "test-job-456"


def test_extract_job_id_not_found():
    """Test extracting job ID when not present."""
    payload = {"status": "ok"}
    assert extract_job_id(payload) is None


def test_unwrap_result_direct_chunks():
    """Test unwrapping result with direct chunks."""
    payload = {"chunks": [{"text": "test"}]}
    result = unwrap_result(payload)
    assert "chunks" in result
    assert len(result["chunks"]) == 1


def test_unwrap_result_nested():
    """Test unwrapping nested result."""
    payload = {"result": {"data": {"chunks": [{"text": "test"}]}}}
    result = unwrap_result(payload)
    assert "chunks" in result


def test_unwrap_result_with_error():
    """Test unwrapping result with error."""
    payload = {
        "result": {
            "success": False,
            "error": {"code": -32603, "message": "Error"},
        }
    }
    result = unwrap_result(payload)
    assert result["success"] is False
    assert "error" in result


def test_parse_chunk_static_from_dict():
    """Test parsing chunk from dictionary."""
    chunk_dict = {
        "uuid": str(uuid.uuid4()),
        "type": "DocBlock",
        "text": "test",
        "body": "test",
        "summary": "summary",
        "sha256": "a" * 64,
        "language": "en",
        "created_at": "2024-01-01T00:00:00+00:00",
        "status": "new",
        "start": 0,
        "end": 4,
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
        "ordinal": 0,
        "chunking_version": "1.0",
    }
    chunk = parse_chunk_static(chunk_dict)
    assert isinstance(chunk, SemanticChunk)
    assert chunk.text == "test"


def test_parse_chunk_static_from_semantic_chunk():
    """Test parsing chunk from SemanticChunk instance."""
    builder = ChunkMetadataBuilder()
    chunk_dict = {
        "uuid": str(uuid.uuid4()),
        "type": "DocBlock",
        "text": "test",
        "body": "test",
        "summary": "summary",
        "sha256": "a" * 64,
        "language": "en",
        "created_at": "2024-01-01T00:00:00+00:00",
        "status": "new",
        "start": 0,
        "end": 4,
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
        "ordinal": 0,
        "chunking_version": "1.0",
    }
    original = builder.json_dict_to_semantic(chunk_dict)
    chunk = parse_chunk_static(original)
    assert chunk is original


def test_extract_chunks_or_raise_success():
    """Test extracting chunks from valid result."""
    result = {
        "chunks": [
            {
                "uuid": str(uuid.uuid4()),
                "type": "DocBlock",
                "text": "test",
                "body": "test",
                "summary": "summary",
                "sha256": "a" * 64,
                "language": "en",
                "created_at": "2024-01-01T00:00:00+00:00",
                "status": "new",
                "start": 0,
                "end": 4,
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
                "ordinal": 0,
                "chunking_version": "1.0",
            }
        ]
    }
    chunks = extract_chunks_or_raise(result)
    assert len(chunks) == 1
    assert isinstance(chunks[0], SemanticChunk)


def test_extract_chunks_or_raise_with_error():
    """Test extracting chunks when result has error."""
    result = {
        "success": False,
        "error": {"code": -32603, "message": "Server error"},
    }
    with pytest.raises(SVOServerError) as exc_info:
        extract_chunks_or_raise(result)
    assert exc_info.value.code == -32603


def test_extract_chunks_or_raise_integrity_error():
    """Test extracting chunks with integrity error."""
    result = {
        "success": False,
        "error": {
            "code": -32603,
            "message": "Integrity error",
            "data": {
                "error": "ChunkingIntegrityError",
                "original_text_length": 100,
                "reconstructed_text_length": 99,
                "chunk_count": 5,
                "integrity_error": "Missing character",
            },
        },
    }
    with pytest.raises(SVOChunkingIntegrityError) as exc_info:
        extract_chunks_or_raise(result)
    assert exc_info.value.original_text_length == 100
    assert exc_info.value.reconstructed_text_length == 99


def test_extract_chunks_or_raise_empty():
    """Test extracting chunks from empty result."""
    result = {}
    with pytest.raises(SVOServerError) as exc_info:
        extract_chunks_or_raise(result)
    assert exc_info.value.code == "empty_result"


def test_extract_chunks_or_raise_empty_list():
    """Test extracting chunks from result with empty list."""
    result = {"chunks": []}
    with pytest.raises(SVOServerError) as exc_info:
        extract_chunks_or_raise(result)
    assert exc_info.value.code == "empty_result"

