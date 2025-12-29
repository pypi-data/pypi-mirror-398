"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Shared exception types for SVO client.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class SVOServerError(Exception):
    """Raised when the SVO server returns an application-level error."""

    def __init__(
        self,
        code: str,
        message: str,
        chunk_error: Optional[Dict[str, Any]] = None,
    ):
        """Initialize SVOServerError.

        Args:
            code: Error code from server.
            message: Error message from server.
            chunk_error: Optional error details dictionary.
        """
        self.code = code
        self.message = message
        self.chunk_error = chunk_error or {}
        super().__init__(f"SVO server error [{code}]: {message}")


class SVOJSONRPCError(Exception):
    """Raised when the SVO server returns a JSON-RPC error response."""

    def __init__(
        self,
        code: int,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        """Initialize SVOJSONRPCError.

        Args:
            code: JSON-RPC error code.
            message: Error message.
            data: Optional error data dictionary.
        """
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(f"JSON-RPC error [{code}]: {message}")


class SVOHTTPError(Exception):
    """Raised when the SVO server returns an HTTP error or invalid response."""

    def __init__(
        self,
        status_code: int,
        message: str,
        response_text: str = "",
    ):
        """Initialize SVOHTTPError.

        Args:
            status_code: HTTP status code.
            message: Error message.
            response_text: Optional response body text.
        """
        self.status_code = status_code
        self.message = message
        self.response_text = response_text
        super().__init__(f"HTTP error [{status_code}]: {message}")


class SVOConnectionError(Exception):
    """Raised when there are network/connection issues with the SVO server."""

    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
    ):
        """Initialize SVOConnectionError.

        Args:
            message: Error message.
            original_error: Optional original exception that caused this error.
        """
        self.message = message
        self.original_error = original_error
        super().__init__(message)


class SVOTimeoutError(Exception):
    """Raised when request to SVO server times out."""

    def __init__(
        self,
        message: str,
        timeout_value: Optional[float] = None,
    ):
        """Initialize SVOTimeoutError.

        Args:
            message: Error message.
            timeout_value: Optional timeout value in seconds.
        """
        self.message = message
        self.timeout_value = timeout_value
        super().__init__(f"Timeout error: {message}")


class SVOEmbeddingError(Exception):
    """Raised when embedding service returns an error or invalid payload."""


class SVOChunkingIntegrityError(SVOServerError):
    """Raised when text integrity check fails after chunking."""

    def __init__(
        self,
        message: str,
        original_text_length: Optional[int] = None,
        reconstructed_text_length: Optional[int] = None,
        chunk_count: Optional[int] = None,
        integrity_error: Optional[str] = None,
        chunk_error: Optional[Dict[str, Any]] = None,
    ):
        """Initialize SVOChunkingIntegrityError.

        Args:
            message: Error message.
            original_text_length: Length of original text.
            reconstructed_text_length: Length of reconstructed text from chunks.
            chunk_count: Number of chunks.
            integrity_error: Optional detailed integrity error message.
            chunk_error: Optional error details dictionary.
        """
        super().__init__(
            code="ChunkingIntegrityError",
            message=message,
            chunk_error=chunk_error or {},
        )
        self.original_text_length = original_text_length
        self.reconstructed_text_length = reconstructed_text_length
        self.chunk_count = chunk_count
        self.integrity_error = integrity_error
