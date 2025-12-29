"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Utilities for parsing chunking results from server responses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from svo_client.errors import SVOServerError, SVOChunkingIntegrityError

if TYPE_CHECKING:
    from chunk_metadata_adapter import SemanticChunk


def parse_chunk_static(chunk: Any, default_type: str = "Draft") -> "SemanticChunk":
    """Parse a chunk from various formats into SemanticChunk.

    Uses factory method from chunk_metadata_adapter for proper deserialization.
    The factory method handles all missing fields, validation, and proper field mapping.

    Args:
        chunk: Chunk data in dict format or SemanticChunk instance.
        default_type: Default chunk type if not present in data (used only if factory method needs it).

    Returns:
        SemanticChunk instance.

    Raises:
        ValueError: If chunk cannot be parsed.
    """
    from chunk_metadata_adapter import SemanticChunk, ChunkMetadataBuilder

    if isinstance(chunk, SemanticChunk):
        return chunk

    if not isinstance(chunk, dict):
        raise ValueError(
            f"Chunk must be dict or SemanticChunk instance, got {type(chunk)}"
        )

    # Prepare chunk data - ensure 'type' is present if missing (required field)
    chunk_data = dict(chunk)
    if "type" not in chunk_data:
        chunk_data["type"] = default_type

    # Map tokens and bm25_tokens from root level to metrics if present
    # Server returns tokens at root level, but SemanticChunk expects them in metrics
    # This ensures tokens are preserved even if adapter doesn't handle the mapping
    # Note: ChunkMetrics expects tokens as List[str], so we need to handle both
    # string lists and dict lists (extracting text from dicts)
    # Also handle case when tokens are already in metrics but in wrong format (dicts instead of strings)
    
    # Ensure metrics dict exists
    if "metrics" not in chunk_data:
        chunk_data["metrics"] = {}
    
    # Helper function to convert tokens to List[str]
    def normalize_tokens(tokens: Any) -> list[str]:
        """Convert tokens to List[str], handling dicts, strings, and other types."""
        if tokens is None:
            return []
        if isinstance(tokens, list):
            if len(tokens) == 0:
                return []
            if isinstance(tokens[0], dict):
                # Extract text field from token dicts
                return [str(t.get("text", t)) for t in tokens]
            elif isinstance(tokens[0], str):
                # Already strings, return as is
                return tokens
            else:
                # Convert to strings if not already
                return [str(t) for t in tokens]
        else:
            # Not a list, convert to list
            return [str(tokens)]
    
    # Handle tokens at root level
    if "tokens" in chunk_data:
        tokens = chunk_data.pop("tokens")
        chunk_data["metrics"]["tokens"] = normalize_tokens(tokens)
    # Handle tokens already in metrics (but might be in wrong format)
    elif "metrics" in chunk_data and isinstance(chunk_data["metrics"], dict):
        if "tokens" in chunk_data["metrics"]:
            tokens = chunk_data["metrics"]["tokens"]
            chunk_data["metrics"]["tokens"] = normalize_tokens(tokens)
    
    # Handle bm25_tokens at root level
    if "bm25_tokens" in chunk_data:
        bm25_tokens = chunk_data.pop("bm25_tokens")
        chunk_data["metrics"]["bm25_tokens"] = normalize_tokens(bm25_tokens)
    # Handle bm25_tokens already in metrics (but might be in wrong format)
    elif "metrics" in chunk_data and isinstance(chunk_data["metrics"], dict):
        if "bm25_tokens" in chunk_data["metrics"]:
            bm25_tokens = chunk_data["metrics"]["bm25_tokens"]
            chunk_data["metrics"]["bm25_tokens"] = normalize_tokens(bm25_tokens)

    try:
        # Use factory method from_dict_with_autofill_and_validation for proper deserialization
        # This method handles autofill, validation, proper field mapping, and all missing fields
        return SemanticChunk.from_dict_with_autofill_and_validation(chunk_data)
    except Exception as exc:  # noqa: BLE001
        # Fallback to builder method if factory method fails
        try:
            builder = ChunkMetadataBuilder()
            return builder.json_dict_to_semantic(chunk_data)
        except Exception as fallback_exc:  # noqa: BLE001
            raise ValueError(
                "Failed to deserialize chunk using chunk_metadata_adapter factory methods: "
                f"{exc}\nFallback also failed: {fallback_exc}\nChunk keys: {list(chunk.keys()) if isinstance(chunk, dict) else 'not a dict'}"
            ) from exc


def extract_job_id(payload: Dict[str, Any]) -> Optional[str]:
    """Extract job ID from response payload.

    Args:
        payload: Response dictionary that may contain job_id.

    Returns:
        Job ID string if found, None otherwise.
    """
    if not isinstance(payload, dict):
        return None
    for key in ("job_id", "jobId"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    nested = payload.get("result")
    if isinstance(nested, dict):
        return extract_job_id(nested)
    return None


def unwrap_result(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Unwrap result from server response.

    Searches recursively for a "chunks" list in the result payload and
    returns a dict containing it. Supports queue envelopes and nested
    result/data wrappers from the adapter.

    Args:
        payload: Server response payload.

    Returns:
        Dictionary containing chunks or error information.

    Raises:
        SVOServerError: If payload is invalid.
    """
    if not isinstance(payload, dict):
        raise SVOServerError(
            code="invalid_result", message="Unexpected response type"
        )

    # Check for error first - if result has success=false, return it as-is
    # so extract_chunks_or_raise can handle it properly
    result = payload.get("result", payload)

    # Handle nested result structure from queue (result.result.result)
    if isinstance(result, dict):
        nested_result = result.get("result")
        if isinstance(nested_result, dict):
            # Check if nested result has success=false (error)
            if nested_result.get("success") is False:
                return nested_result
            # Otherwise use nested result for chunk search
            result = nested_result

    # Check for error in final result
    if isinstance(result, dict) and result.get("success") is False:
        return result

    def _find_chunks(obj: Any) -> Optional[List[Any]]:
        """Recursively search for chunks list in nested structure.

        Args:
            obj: Object to search (dict, list, or other).

        Returns:
            List of chunks if found, None otherwise.
        """
        if isinstance(obj, dict):
            chunks = obj.get("chunks")
            if isinstance(chunks, list):
                return chunks
            for value in obj.values():
                found = _find_chunks(value)
                if found is not None:
                    return found
        return None

    chunks = _find_chunks(result)
    if chunks is not None:
        return {"chunks": chunks}

    if not isinstance(result, dict):
        raise SVOServerError(
            code="invalid_result",
            message="Result is not a dict",
        )

    return result


def extract_chunks_or_raise(
    result: Dict[str, Any],
) -> List["SemanticChunk"]:
    """Extract chunks from result, handling multiple response formats.

    Searches for chunks at different nesting levels:
    1. result["chunks"]
    2. result["data"]["chunks"]
    3. result["result"]["chunks"]
    4. result["data"]["result"]["chunks"]

    Args:
        result: Result dictionary from server.

    Returns:
        List of parsed SemanticChunk objects.

    Raises:
        SVOServerError: If result contains error or chunks cannot be extracted.
        SVOChunkingIntegrityError: If integrity error is detected.
    """
    # Check for error first
    if result.get("success") is False:
        error = result.get("error", {}) or {}
        error_code = error.get("code", "server_error")
        error_message = error.get(
            "message",
            "Server returned success=false",
        )

        # Check if it's an integrity error
        error_data = error.get("data", {})
        if isinstance(error_data, dict) and error_data.get("error") == "ChunkingIntegrityError":
            raise SVOChunkingIntegrityError(
                message=error_message,
                original_text_length=error_data.get("original_text_length"),
                reconstructed_text_length=error_data.get("reconstructed_text_length"),
                chunk_count=error_data.get("chunk_count"),
                integrity_error=error_data.get("integrity_error"),
                chunk_error=error,
            )

        raise SVOServerError(
            code=error_code,
            message=error_message,
            chunk_error=error,
        )

    # Try to find chunks at different levels
    chunks = None

    # Level 1: Direct chunks
    chunks = result.get("chunks")
    if isinstance(chunks, list) and len(chunks) > 0:
        pass  # Found, continue below
    else:
        # Level 2: result["data"]["chunks"]
        data = result.get("data", {})
        if isinstance(data, dict):
            chunks = data.get("chunks")
            if isinstance(chunks, list) and len(chunks) > 0:
                pass  # Found, continue below
            else:
                # Level 3: result["data"]["result"]["chunks"]
                nested_result = data.get("result", {})
                if isinstance(nested_result, dict):
                    chunks = nested_result.get("chunks")
                    if isinstance(chunks, list) and len(chunks) > 0:
                        pass  # Found, continue below
                    else:
                        # Level 4: nested data -> result -> result -> data
                        deeper_result = nested_result.get("result", {})
                        if isinstance(deeper_result, dict):
                            deeper_data = deeper_result.get("data", {})
                            if isinstance(deeper_data, dict):
                                chunks = deeper_data.get("chunks")

    # Validate chunks
    if not isinstance(chunks, list):
        # Log structure for debugging
        import logging

        logger = logging.getLogger(__name__)
        has_data = bool(isinstance(result, dict) and "data" in result)
        has_result = bool(isinstance(result, dict) and "result" in result)
        logger.debug(
            "Failed to extract chunks. Result structure: %s",
            {
                "keys": (
                    list(result.keys())
                    if isinstance(result, dict)
                    else "not a dict"
                ),
                "has_data": has_data,
                "has_result": has_result,
            },
        )
        raise SVOServerError(
            code="empty_result",
            message="Empty or invalid result from server",
        )

    if len(chunks) == 0:
        raise SVOServerError(
            code="empty_result",
            message="Empty chunks list from server",
        )

    # Parse chunks
    parsed_chunks: List["SemanticChunk"] = []
    # Try to extract default type from result if available
    default_type = result.get("type", "Draft")
    if isinstance(default_type, dict):
        default_type = "Draft"

    for chunk in chunks:
        if isinstance(chunk, dict) and "error" in chunk:
            err = chunk["error"]
            raise SVOServerError(
                code=err.get("code", "unknown"),
                message=err.get("message", str(err)),
                chunk_error=err,
            )
        # Try to get type from chunk params if available
        chunk_type = default_type
        if isinstance(chunk, dict):
            # Check if type is in chunk itself
            if "type" in chunk:
                chunk_type = chunk["type"]
            # Or check in nested structure
            elif "params" in chunk and isinstance(chunk["params"], dict):
                chunk_type = chunk["params"].get("type", default_type)

        parsed_chunks.append(parse_chunk_static(chunk, default_type=chunk_type))
    return parsed_chunks
