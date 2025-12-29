"""
Tests for text_utils module.
"""

import uuid

import pytest
from chunk_metadata_adapter import ChunkMetadataBuilder, SemanticChunk

from svo_client.errors import SVOChunkingIntegrityError
from svo_client.text_utils import reconstruct_text, verify_text_integrity


def make_chunk(text: str, ordinal: int) -> SemanticChunk:
    """Create a test chunk."""
    builder = ChunkMetadataBuilder()
    chunk_dict = {
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
    return builder.json_dict_to_semantic(chunk_dict)


def test_reconstruct_text():
    """Test text reconstruction from chunks."""
    chunks = [
        make_chunk("Hello ", 0),
        make_chunk("world", 1),
        make_chunk("!", 2),
    ]
    result = reconstruct_text(chunks)
    assert result == "Hello world!"


def test_reconstruct_text_ordered():
    """Test text reconstruction respects ordinal."""
    chunks = [
        make_chunk("world", 1),
        make_chunk("!", 2),
        make_chunk("Hello ", 0),
    ]
    result = reconstruct_text(chunks)
    assert result == "Hello world!"


def test_verify_text_integrity_success():
    """Test successful integrity verification."""
    chunks = [
        make_chunk("Hello ", 0),
        make_chunk("world", 1),
    ]
    original = "Hello world"
    result = verify_text_integrity(chunks, original)
    assert result is True


def test_verify_text_integrity_failure():
    """Test integrity verification failure."""
    chunks = [
        make_chunk("Hello", 0),
        make_chunk("world", 1),
    ]
    original = "Hello world"  # Missing space
    with pytest.raises(SVOChunkingIntegrityError) as exc_info:
        verify_text_integrity(chunks, original)
    assert exc_info.value.original_text_length == 11
    assert exc_info.value.reconstructed_text_length == 10
    assert exc_info.value.chunk_count == 2


def test_verify_text_integrity_empty_chunks():
    """Test integrity verification with empty chunks."""
    chunks = []
    original = "test"
    with pytest.raises(SVOChunkingIntegrityError):
        verify_text_integrity(chunks, original)

