"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests for example_usage wired to adapter-based client.
"""

import asyncio
import uuid

import pytest

from svo_client import (
    ChunkerClient,
    SVOConnectionError,
    SVOHTTPError,
    SVOJSONRPCError,
    SVOServerError,
    SVOTimeoutError,
)
from chunk_metadata_adapter import SemanticChunk

class FakeClient:
    """Test double for ChunkerClient used in example_usage tests."""

    def __init__(self, chunk_fn, health_fn=None, help_fn=None):
        self._chunk_fn = chunk_fn
        self._health_fn = health_fn or (lambda: {"status": "ok"})
        self._help_fn = help_fn or (lambda: {"help": "info"})

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def chunk_text(self, *args, **kwargs):
        return await self._chunk_fn()

    async def health(self, *args, **kwargs):
        return await self._health_fn()

    async def get_help(self, *args, **kwargs):
        return await self._help_fn()

    def reconstruct_text(self, chunks):
        return ""

@pytest.mark.asyncio
async def test_example_usage(monkeypatch):
    # Мокаем методы клиента
    async def fake_chunk_text(self, text, **params):
        return [SemanticChunk(
            uuid="11111111-1111-4111-8111-111111111111",
            text="Hello, ",
            body="Hello, ",
            summary="summary",
            sha256="a"*64,
            ordinal=0,
            type="DocBlock",
            language="en",
            start=0,
            end=6,
            created_at="2024-01-01T00:00:00+00:00",
            status="new",
            task_id=str(uuid.uuid4()),
            subtask_id=str(uuid.uuid4()),
            unit_id=str(uuid.uuid4())
        ),
        SemanticChunk(
            uuid="22222222-2222-4222-8222-222222222222",
            text="world!",
            body="world!",
            summary="summary",
            sha256="b"*64,
            ordinal=1,
            type="DocBlock",
            language="en",
            start=0,
            end=6,
            created_at="2024-01-01T00:00:00+00:00",
            status="new",
            task_id=str(uuid.uuid4()),
            subtask_id=str(uuid.uuid4()),
            unit_id=str(uuid.uuid4())
        )]
    async def fake_health(self):
        return {"status": "ok"}
    async def fake_get_help(self, cmdname=None):
        return {"help": "info"}
    # Подмена методов
    monkeypatch.setattr(ChunkerClient, "chunk_text", fake_chunk_text)
    monkeypatch.setattr(ChunkerClient, "health", fake_health)
    monkeypatch.setattr(ChunkerClient, "get_help", fake_get_help)

    async with ChunkerClient() as client:
        chunks = await client.chunk_text("test")
        assert isinstance(chunks, list)
        assert all(isinstance(c, SemanticChunk) for c in chunks)
        text = client.reconstruct_text(chunks)
        assert text == "Hello, world!"
        health = await client.health()
        assert health["status"] == "ok"
        help_info = await client.get_help()
        assert help_info["help"] == "info"

def test_example_usage_handles_validation_error(monkeypatch, capsys):
    import svo_client.examples.example_usage as example_usage
    from chunk_metadata_adapter import SemanticChunk
    def fake_validate_and_fill(data):
        return None, {'error': 'Fake validation error', 'fields': {}}
    monkeypatch.setattr(SemanticChunk, "validate_and_fill", staticmethod(fake_validate_and_fill))
    # Патчим chunk_text, чтобы выбрасывал ValueError
    async def fake_chunk_text(*args, **kwargs):
        raise ValueError("Chunk does not validate against chunk_metadata_adapter.SemanticChunk: Fake validation error")
    monkeypatch.setattr(
        example_usage,
        "ChunkerClient",
        lambda *a, **k: FakeClient(chunk_fn=fake_chunk_text),
    )
    import asyncio
    asyncio.run(example_usage.main())
    out = capsys.readouterr().out
    assert "Validation error:" in out 

def test_example_usage_handles_server_error(monkeypatch, capsys):
    import svo_client.examples.example_usage as example_usage
    # Патчим chunk_text, чтобы выбрасывал SVOServerError
    async def fake_chunk_text(*args, **kwargs):
        raise SVOServerError("sha256_mismatch", "SHA256 mismatch: original=..., chunks=...", {"code": "sha256_mismatch", "message": "SHA256 mismatch: original=..., chunks=..."})
    monkeypatch.setattr(
        example_usage,
        "ChunkerClient",
        lambda *a, **k: FakeClient(chunk_fn=fake_chunk_text),
    )
    import asyncio
    asyncio.run(example_usage.main())
    out = capsys.readouterr().out
    assert "SVO server error:" in out
    assert "sha256_mismatch" in out

def test_example_usage_handles_jsonrpc_error(monkeypatch, capsys):
    import svo_client.examples.example_usage as example_usage
    # Патчим chunk_text, чтобы выбрасывал SVOJSONRPCError
    async def fake_chunk_text(*args, **kwargs):
        raise SVOJSONRPCError(-32602, "Invalid params", {"details": "test"})
    async def fake_health(*args, **kwargs):
        raise SVOJSONRPCError(-32603, "Internal error")
    async def fake_get_help(*args, **kwargs):
        raise SVOJSONRPCError(-32601, "Method not found")
    monkeypatch.setattr(
        example_usage,
        "ChunkerClient",
        lambda *a, **k: FakeClient(
            chunk_fn=fake_chunk_text,
            health_fn=fake_health,
            help_fn=fake_get_help,
        ),
    )
    import asyncio
    asyncio.run(example_usage.main())
    out = capsys.readouterr().out
    assert "JSON-RPC error:" in out
    assert "Invalid params" in out
    assert "Health check error:" in out
    assert "Internal error" in out
    assert "Help error:" in out
    assert "Method not found" in out

def test_example_usage_handles_http_error(monkeypatch, capsys):
    import svo_client.examples.example_usage as example_usage
    # Патчим методы, чтобы выбрасывали SVOHTTPError
    async def fake_chunk_text(*args, **kwargs):
        raise SVOHTTPError(500, "Internal Server Error", "Server details")
    async def fake_health(*args, **kwargs):
        raise SVOHTTPError(503, "Service Unavailable")
    async def fake_get_help(*args, **kwargs):
        raise SVOHTTPError(404, "Not Found")
    monkeypatch.setattr(
        example_usage,
        "ChunkerClient",
        lambda *a, **k: FakeClient(
            chunk_fn=fake_chunk_text,
            health_fn=fake_health,
            help_fn=fake_get_help,
        ),
    )
    import asyncio
    asyncio.run(example_usage.main())
    out = capsys.readouterr().out
    assert "HTTP error:" in out
    assert "Internal Server Error" in out
    assert "Health check error:" in out
    assert "Service Unavailable" in out
    assert "Help error:" in out
    assert "Not Found" in out

def test_example_usage_handles_connection_error(monkeypatch, capsys):
    import svo_client.examples.example_usage as example_usage
    # Патчим методы, чтобы выбрасывали SVOConnectionError
    async def fake_chunk_text(*args, **kwargs):
        raise SVOConnectionError("Connection refused", OSError("Connection refused"))
    async def fake_health(*args, **kwargs):
        raise SVOConnectionError("Network unreachable")
    async def fake_get_help(*args, **kwargs):
        raise SVOConnectionError("Server disconnected")
    monkeypatch.setattr(
        example_usage,
        "ChunkerClient",
        lambda *a, **k: FakeClient(
            chunk_fn=fake_chunk_text,
            health_fn=fake_health,
            help_fn=fake_get_help,
        ),
    )
    import asyncio
    asyncio.run(example_usage.main())
    out = capsys.readouterr().out
    assert "Connection error:" in out
    assert "Connection refused" in out
    assert "Health check error:" in out
    assert "Network unreachable" in out
    assert "Help error:" in out
    assert "Server disconnected" in out

def test_example_usage_handles_timeout_error(monkeypatch, capsys):
    import svo_client.examples.example_usage as example_usage
    # Патчим методы, чтобы выбрасывали SVOTimeoutError
    async def fake_chunk_text(*args, **kwargs):
        raise SVOTimeoutError("Request timed out after 60s", 60.0)
    async def fake_health(*args, **kwargs):
        raise SVOTimeoutError("Health check timed out", 30.0)
    async def fake_get_help(*args, **kwargs):
        raise SVOTimeoutError("Help request timed out", 15.0)
    monkeypatch.setattr(
        example_usage,
        "ChunkerClient",
        lambda *a, **k: FakeClient(
            chunk_fn=fake_chunk_text,
            health_fn=fake_health,
            help_fn=fake_get_help,
        ),
    )
    import asyncio
    asyncio.run(example_usage.main())
    out = capsys.readouterr().out
    assert "Timeout error:" in out
    assert "Request timed out after 60s" in out
    assert "Health check error:" in out
    assert "Health check timed out" in out
    assert "Help error:" in out
    assert "Help request timed out" in out 