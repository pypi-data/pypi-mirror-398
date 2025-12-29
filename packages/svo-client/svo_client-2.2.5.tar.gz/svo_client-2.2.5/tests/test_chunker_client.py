"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests for adapter-based ChunkerClient.
"""

import asyncio
import uuid
from typing import Any, Dict

import pytest

from svo_client import (
    ChunkerClient,
    SVOConnectionError,
    SVOJSONRPCError,
    SVOServerError,
    SVOTimeoutError,
)


def make_valid_chunk_dict(text: str, ordinal: int) -> Dict[str, Any]:
    """Build minimal valid chunk dict for chunk_metadata_adapter."""
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


class StubAdapter:
    """Simple stub for JsonRpcClient methods used by ChunkerClient."""

    def __init__(self, responses: Dict[str, Any]):
        self.responses = responses
        self.calls = []

    async def execute_command(
        self,
        command: str,
        params: Dict[str, Any] | None = None,
        use_cmd_endpoint: bool = False,
    ):
        """Execute command via JSON-RPC."""
        self.calls.append(("execute_command", command, params, use_cmd_endpoint))
        value = self.responses.get(command)
        if isinstance(value, Exception):
            raise value
        # Return in format expected by ChunkerClient
        if isinstance(value, dict) and "result" not in value:
            return {"result": value}
        return value or {"result": {"success": True}}

    async def execute_command_unified(
        self,
        command: str,
        params: Dict[str, Any] | None = None,
        *,
        use_cmd_endpoint: bool = False,
        expect_queue: bool = False,
        auto_poll: bool = False,
        poll_interval: float = 1.0,
        timeout: float | None = None,
    ):
        """Execute command with unified queue handling."""
        self.calls.append(
            (
                "execute_command_unified",
                command,
                params,
                expect_queue,
                auto_poll,
            )
        )
        value = self.responses.get(command)
        if isinstance(value, Exception):
            raise value
        # Return in format expected by ChunkerClient
        if isinstance(value, dict):
            # If expect_queue and auto_poll, return final result
            if expect_queue and auto_poll:
                if "result" not in value:
                    return {"result": value}
                return value
            # If expect_queue but no auto_poll, return job_id
            if expect_queue and not auto_poll:
                job_id = value.get("job_id") or "test-job-123"
                return {"result": {"job_id": job_id}}
        return value or {"result": {"success": True, "chunks": []}}

    async def cmd_call(self, command: str, params: Dict[str, Any] | None = None, validate: bool = False):
        self.calls.append(("cmd", command, params, validate))
        value = self.responses.get(command)
        if isinstance(value, Exception):
            raise value
        return value

    async def queue_add_job(self, job_type: str, job_id: str, params: Dict[str, Any]):
        self.calls.append(("queue_add_job", job_type, job_id, params))
        value = self.responses.get("queue_add_job")
        if isinstance(value, Exception):
            raise value
        return value or {"success": True, "job_id": job_id}

    async def queue_get_job_status(self, job_id: str):
        self.calls.append(("queue_get_job_status", job_id))
        value = self.responses.get("queue_get_job_status")
        if isinstance(value, Exception):
            raise value
        return value or {"job_id": job_id, "status": "pending"}

    async def queue_get_job_logs(self, job_id: str):
        self.calls.append(("queue_get_job_logs", job_id))
        value = self.responses.get("queue_get_job_logs")
        if isinstance(value, Exception):
            raise value
        return value or {"job_id": job_id, "stdout": [], "stderr": []}

    async def get_openapi_schema(self):
        value = self.responses.get("openapi")
        if isinstance(value, Exception):
            raise value
        return value or {"openapi": "3.0.2"}

    async def close(self):
        return None


@pytest.mark.asyncio
async def test_chunk_text_success():
    chunk_payload = {"success": True, "chunks": [make_valid_chunk_dict("hello", 0), make_valid_chunk_dict("world", 1)]}
    stub = StubAdapter({"chunk": chunk_payload})
    client = ChunkerClient()
    client._client = stub  # type: ignore[attr-defined]

    chunks = await client.chunk_text("hello world")

    assert len(chunks) == 2
    assert client.reconstruct_text(chunks) == "helloworld"
    assert stub.calls[0][0] == "execute_command_unified"
    assert stub.calls[0][1] == "chunk"


@pytest.mark.asyncio
async def test_chunk_text_success_false():
    stub = StubAdapter({"chunk": {"success": False, "error": {"code": "validation_error", "message": "bad"}}})
    client = ChunkerClient()
    client._client = stub  # type: ignore[attr-defined]

    with pytest.raises(SVOServerError) as excinfo:
        await client.chunk_text("text")

    assert excinfo.value.code == "validation_error"


@pytest.mark.asyncio
async def test_chunk_text_chunk_error_entry():
    stub = StubAdapter({"chunk": {"success": True, "chunks": [{"error": {"code": "sha256_mismatch", "message": "bad"}}]}})
    client = ChunkerClient()
    client._client = stub  # type: ignore[attr-defined]

    with pytest.raises(SVOServerError) as excinfo:
        await client.chunk_text("text")

    assert excinfo.value.code == "sha256_mismatch"


@pytest.mark.asyncio
async def test_chunk_text_empty_result():
    # Return result without chunks list (should trigger error)
    stub = StubAdapter({"chunk": {"result": {"success": True}}})
    client = ChunkerClient()
    client._client = stub  # type: ignore[attr-defined]

    with pytest.raises(SVOServerError) as excinfo:
        await client.chunk_text("text")
    
    assert excinfo.value.code == "empty_result"


@pytest.mark.asyncio
async def test_get_help_and_health_success():
    stub = StubAdapter(
        {
            "help": {"success": True, "commands": {"chunk": {}}},
            "health": {"success": True, "status": "ok"},
        }
    )
    client = ChunkerClient()
    client._client = stub  # type: ignore[attr-defined]

    help_info = await client.get_help()
    health = await client.health()

    # execute_command returns {"result": value}
    assert isinstance(help_info, dict)
    assert isinstance(health, dict)


@pytest.mark.asyncio
async def test_jsonrpc_error_mapping():
    stub = StubAdapter({"chunk": RuntimeError("Invalid params")})
    client = ChunkerClient()
    client._client = stub  # type: ignore[attr-defined]
    
    with pytest.raises(SVOJSONRPCError):
        await client.chunk_text("text")
    

@pytest.mark.asyncio
async def test_timeout_mapping():
    stub = StubAdapter({"chunk": asyncio.TimeoutError("timeout")})
    client = ChunkerClient()
    client._client = stub  # type: ignore[attr-defined]
    
    with pytest.raises(SVOTimeoutError):
        await client.chunk_text("text")
    

@pytest.mark.asyncio
async def test_connection_error_mapping():
    stub = StubAdapter({"chunk": ConnectionError("boom")})
    client = ChunkerClient()
    client._client = stub  # type: ignore[attr-defined]
    
    with pytest.raises(SVOConnectionError):
        await client.chunk_text("text")
    

@pytest.mark.asyncio
async def test_openapi_schema():
    stub = StubAdapter({"openapi": {"openapi": "3.1.0"}})
    client = ChunkerClient()
    client._client = stub  # type: ignore[attr-defined]

    schema = await client.get_openapi_schema()
    
    assert schema["openapi"] == "3.1.0"
    

@pytest.mark.asyncio
async def test_queue_chunk_text_transparency():
    """Test submit_chunk_job method."""
    stub = StubAdapter({"chunk": {"job_id": "test-job-123"}})
    client = ChunkerClient()
    client._client = stub  # type: ignore[attr-defined]

    job_id = await client.submit_chunk_job("text", type="Draft")

    assert job_id == "test-job-123"
    assert len(stub.calls) > 0
    assert stub.calls[0][0] == "execute_command_unified"


@pytest.mark.asyncio
async def test_queue_status_and_logs():
    """Test get_job_status and get_job_logs methods."""
    stub = StubAdapter(
        {
            "queue_get_job_status": {"job_id": "j1", "status": "done", "data": {"status": "completed"}},
            "queue_get_job_logs": {"job_id": "j1", "stdout": ["ok"], "stderr": []},
        }
    )
    client = ChunkerClient()
    client._client = stub  # type: ignore[attr-defined]

    status = await client.get_job_status("j1")
    logs = await client.get_job_logs("j1")

    assert status["status"] == "done"
    assert logs["stdout"] == ["ok"]
