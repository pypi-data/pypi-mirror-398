"""
Tests for error_mapper module.
"""

import asyncio

import pytest

from svo_client.error_mapper import map_exception
from svo_client.errors import (
    SVOChunkingIntegrityError,
    SVOConnectionError,
    SVOHTTPError,
    SVOJSONRPCError,
    SVOTimeoutError,
)


def test_map_timeout_error():
    """Test mapping timeout error."""
    exc = asyncio.TimeoutError("Timeout")
    mapped = map_exception(exc, timeout=30.0)
    assert isinstance(mapped, SVOTimeoutError)
    assert mapped.timeout_value == 30.0


def test_map_http_error():
    """Test mapping HTTP error."""
    class MockResponse:
        status_code = 500
        text = "Internal Server Error"
    
    class MockHTTPError(Exception):
        def __init__(self):
            self.response = MockResponse()
            super().__init__("HTTP 500")
    
    exc = MockHTTPError()
    mapped = map_exception(exc, timeout=30.0)
    assert isinstance(mapped, SVOHTTPError)
    assert mapped.status_code == 500
    assert mapped.response_text == "Internal Server Error"


def test_map_integrity_error():
    """Test mapping integrity error."""
    class MockIntegrityError(RuntimeError):
        def __init__(self):
            self.data = {
                "error": "ChunkingIntegrityError",
                "original_text_length": 100,
                "reconstructed_text_length": 99,
                "chunk_count": 5,
                "integrity_error": "Missing character",
            }
            super().__init__("Integrity check failed")
    
    exc = MockIntegrityError()
    mapped = map_exception(exc, timeout=30.0)
    assert isinstance(mapped, SVOChunkingIntegrityError)
    assert mapped.original_text_length == 100
    assert mapped.reconstructed_text_length == 99
    assert mapped.chunk_count == 5


def test_map_jsonrpc_error():
    """Test mapping JSON-RPC error."""
    exc = RuntimeError("JSON-RPC error")
    mapped = map_exception(exc, timeout=30.0)
    assert isinstance(mapped, SVOJSONRPCError)
    assert mapped.code == -32603


def test_map_connection_error():
    """Test mapping connection error."""
    exc = ConnectionError("Connection refused")
    mapped = map_exception(exc, timeout=30.0)
    assert isinstance(mapped, SVOConnectionError)
    assert "Connection refused" in str(mapped)

