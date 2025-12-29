"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Text utilities for chunking operations.
"""

from typing import TYPE_CHECKING, List

from svo_client.errors import SVOChunkingIntegrityError

if TYPE_CHECKING:
    from chunk_metadata_adapter import SemanticChunk


def verify_text_integrity(chunks: List["SemanticChunk"], original_text: str) -> bool:
    """Verify that chunks reconstruct original text.

    Args:
        chunks: List of SemanticChunk objects.
        original_text: Original text that was chunked.

    Returns:
        True if integrity check passes.

    Raises:
        SVOChunkingIntegrityError: If chunks don't reconstruct original text.
    """
    reconstructed = "".join(chunk.body for chunk in chunks if chunk.body is not None)
    if reconstructed != original_text:
        raise SVOChunkingIntegrityError(
            message="Client-side text integrity check failed",
            original_text_length=len(original_text),
            reconstructed_text_length=len(reconstructed),
            chunk_count=len(chunks),
            integrity_error="Reconstructed text does not match original",
        )
    return True


def reconstruct_text(chunks: List["SemanticChunk"]) -> str:
    """Reconstruct original text from SemanticChunk list.

    Args:
        chunks: List of SemanticChunk objects.

    Returns:
        Reconstructed text string.
    """
    sorted_chunks = sorted(
        chunks,
        key=lambda c: (
            c.ordinal
            if getattr(c, "ordinal", None) is not None
            else chunks.index(c)
        ),
    )
    # fmt: off
    texts = (
        chunk.text
        for chunk in sorted_chunks
        if getattr(chunk, "text", None)
    )
    # fmt: on
    return "".join(texts)

