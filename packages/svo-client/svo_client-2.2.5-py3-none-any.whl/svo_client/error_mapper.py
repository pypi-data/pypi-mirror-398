"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Error mapping utilities for ChunkerClient.
"""

import asyncio
from typing import Any, Dict

from svo_client.errors import (
    SVOChunkingIntegrityError,
    SVOConnectionError,
    SVOHTTPError,
    SVOJSONRPCError,
    SVOTimeoutError,
)


def map_exception(exc: Exception, timeout: float) -> Exception:
    """Convert transport-level exceptions to domain-specific errors.

    Args:
        exc: Original exception.
        timeout: Timeout value in seconds.

    Returns:
        Mapped domain-specific exception.
    """
    name = type(exc).__name__.lower()
    if isinstance(exc, asyncio.TimeoutError) or "timeout" in name:
        return SVOTimeoutError(str(exc), timeout_value=timeout)
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None) if response else None
    if status:
        response_text = getattr(response, "text", "") or ""
        return SVOHTTPError(
            status_code=status,
            message=str(exc),
            response_text=str(response_text),
        )
    if isinstance(exc, RuntimeError):
        # Check if it's an integrity error
        error_str = str(exc).lower()
        if "integrity" in error_str:
            error_data = getattr(exc, "data", {}) or {}
            if isinstance(error_data, dict) and error_data.get("error") == "ChunkingIntegrityError":
                return SVOChunkingIntegrityError(
                    message=str(exc),
                    original_text_length=error_data.get("original_text_length"),
                    reconstructed_text_length=error_data.get("reconstructed_text_length"),
                    chunk_count=error_data.get("chunk_count"),
                    integrity_error=error_data.get("integrity_error"),
                )
        return SVOJSONRPCError(code=-32603, message=str(exc))
    return SVOConnectionError(f"Connection error: {exc}", exc)

