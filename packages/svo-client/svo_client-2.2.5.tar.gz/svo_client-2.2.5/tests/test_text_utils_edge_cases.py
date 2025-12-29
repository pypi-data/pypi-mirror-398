"""
Edge case tests for text_utils to achieve 90%+ coverage.
"""

import uuid

import pytest
from chunk_metadata_adapter import ChunkMetadataBuilder

from svo_client.errors import SVOChunkingIntegrityError
from svo_client.text_utils import reconstruct_text, verify_text_integrity


def make_chunk(text: str, ordinal: int):
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


def test_reconstruct_text_with_body():
    """Test reconstruct_text using body field."""
    chunks = [
        make_chunk("Hello ", 0),
        make_chunk("world", 1),
    ]
    result = reconstruct_text(chunks)
    assert result == "Hello world"


def test_verify_text_integrity_with_body():
    """Test verify_text_integrity using body field."""
    chunks = [
        make_chunk("Hello ", 0),
        make_chunk("world", 1),
    ]
    original = "Hello world"
    result = verify_text_integrity(chunks, original)
    assert result is True

