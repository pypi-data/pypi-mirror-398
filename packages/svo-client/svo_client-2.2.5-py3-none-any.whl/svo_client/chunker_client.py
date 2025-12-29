"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Async adapter-only client for SVO semantic chunker.
Always executes `chunk` via queue and exposes one-shot call plus
explicit queue helpers.
"""

# mypy: disable-error-code=import-untyped

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# Removed embed_client dependency - using local config generation
from mcp_proxy_adapter.client.jsonrpc_client import (
    JsonRpcClient,
)  # type: ignore[import-untyped]
from mcp_proxy_adapter.client.jsonrpc_client.transport import (
    JsonRpcTransport,
)  # type: ignore[import-untyped]
from svo_client.config_loader import ConfigLoader
from svo_client.config_utils import config_to_client_kwargs
from svo_client.error_mapper import map_exception
from svo_client.errors import (
    SVOChunkingIntegrityError,
    SVOServerError,
    SVOTimeoutError,
)
from svo_client.result_parser import (
    extract_chunks_or_raise,
    extract_job_id,
    unwrap_result,
)
from svo_client.text_utils import reconstruct_text, verify_text_integrity

if TYPE_CHECKING:
    from chunk_metadata_adapter import (  # type: ignore[import-untyped]
        SemanticChunk,
    )


class ChunkerClient:
    """Adapter-only client with queued chunk execution."""

    def __init__(
        self,
        *,
        config: Optional[Dict[str, Any]] = None,
        host: str = "localhost",
        port: int = 8009,
        cert: Optional[str] = None,
        key: Optional[str] = None,
        ca: Optional[str] = None,
        token: Optional[str] = None,
        token_header: str = "X-API-Key",
        check_hostname: bool = False,
        timeout: Optional[float] = None,
        poll_interval: float = 1.0,
    ):
        """Initialize ChunkerClient.

        Args:
            config: Optional pre-built configuration dict. If provided, other params are ignored.
            host: Server hostname or IP address.
            port: Server port number.
            cert: Path to client certificate file (for mTLS).
            key: Path to client private key file (for mTLS).
            ca: Path to CA certificate file (for mTLS).
            token: API token for authentication.
            token_header: HTTP header name for token authentication.
            check_hostname: Whether to verify hostname in SSL certificate.
            timeout: Request timeout in seconds. None means no timeout.
            poll_interval: Interval between job status polls in seconds.
        """
        # Resolve config with priority: CLI/API > env vars > config file
        cfg = config or ConfigLoader.resolve_config(
            host=host,
            port=port,
            cert=cert,
            key=key,
            ca=ca,
            token=token,
            token_header=token_header,
            check_hostname=check_hostname,
            timeout=timeout,
        )

        # Get timeout from config if not provided via API
        config_timeout = cfg.get("timeout")
        if timeout is None and config_timeout is not None:
            timeout = config_timeout

        protocol, client_kwargs = config_to_client_kwargs(
            cfg, check_hostname=check_hostname
        )
        self.protocol = protocol
        self.host = client_kwargs["host"]
        self.port = client_kwargs["port"]
        self.timeout = timeout  # None means no timeout
        self.poll_interval = poll_interval

        self._client = JsonRpcClient(**client_kwargs)
        if isinstance(self._client, JsonRpcTransport):
            # Set timeout only if provided (None means no timeout)
            if timeout is not None:
                self._client.timeout = timeout


    async def close(self) -> None:
        """Close the underlying adapter client."""
        await self._client.close()

    async def __aenter__(self) -> "ChunkerClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()



    async def get_openapi_schema(self) -> Dict[str, Any]:
        """Fetch OpenAPI schema using adapter transport."""
        try:
            return await self._client.get_openapi_schema()
        except Exception as exc:  # noqa: BLE001
            mapped = map_exception(exc, self.timeout)
            raise mapped from exc

    async def submit_chunk_job(self, text: str, **params: Any) -> str:
        try:
            result = await self._client.execute_command_unified(
                "chunk",
                {"text": text, **params},
                expect_queue=True,
                auto_poll=False,
            )
        except Exception as exc:  # noqa: BLE001
            raise map_exception(exc, self.timeout) from exc

        job_id = extract_job_id(result)
        if not job_id:
            raise SVOServerError(
                code="no_job_id", message="Chunk command did not return job_id"
            )
        return job_id

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Fetch job status via adapter."""
        try:
            return await self._client.queue_get_job_status(job_id)
        except Exception as exc:  # noqa: BLE001
            raise map_exception(exc, self.timeout) from exc

    async def get_job_logs(self, job_id: str) -> Dict[str, Any]:
        """Fetch job logs via adapter queue API."""
        try:
            return await self._client.queue_get_job_logs(job_id)
        except Exception as exc:  # noqa: BLE001
            raise map_exception(exc, self.timeout) from exc

    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List jobs from queue.

        Args:
            status: Filter by job status (optional).
            limit: Maximum number of jobs to return (optional).

        Returns:
            List of job dictionaries with status information.

        Raises:
            SVOServerError: If server returns an error.
            SVOConnectionError: If connection fails.
        """
        try:
            params: Dict[str, Any] = {}
            if status:
                params["status"] = status
            # Note: limit parameter may not be supported by all server versions
            # Skip limit for now to ensure compatibility
            # if limit:
            #     params["limit"] = limit

            result = await self._client.queue_list_jobs(**params)
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                # Handle wrapped response
                jobs = result.get("jobs", result.get("data", []))
                if isinstance(jobs, list):
                    return jobs
                return []
            return []
        except Exception as exc:  # noqa: BLE001
            raise map_exception(exc, self.timeout) from exc

    async def wait_for_result(
        self,
        job_id: str,
        *,
        poll_interval: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> List["SemanticChunk"]:
        """Wait for job completion and return chunks.

        Args:
            job_id: Job identifier from submit_chunk_job.
            poll_interval: Interval between status polls in seconds.
            timeout: Maximum time to wait in seconds.

        Returns:
            List of SemanticChunk objects.

        Raises:
            SVOTimeoutError: If job does not complete within timeout.
            SVOServerError: If job fails or server returns an error.
            SVOChunkingIntegrityError: If integrity check fails.
        """
        interval = poll_interval or self.poll_interval
        deadline = time.monotonic() + timeout if timeout else None
        pending = {"queued", "pending", "running", "processing", "started"}

        while True:
            try:
                status = await self._client.queue_get_job_status(job_id)
            except Exception as exc:  # noqa: BLE001
                raise map_exception(exc, self.timeout) from exc

            if isinstance(status, dict):
                data = status.get("data", status)
            else:
                data = {}
            status_raw = data.get("status") or data.get("state") or ""
            status_value = str(status_raw).lower()
            if not status_value and isinstance(status, dict):
                status_value = str(status.get("status") or "").lower()

            if status_value in pending:
                if deadline and time.monotonic() >= deadline:
                    # fmt: off
                    message = (
                        f"Job {job_id} did not finish in "
                        f"{timeout} seconds"
                    )
                    # fmt: on
                    raise SVOTimeoutError(message, timeout)
                await asyncio.sleep(interval)
                continue

            # Final state
            if isinstance(data, dict) and data.get("success") is False:
                error = data.get("error", {}) or {}
                error_data = error.get("data", {})
                # Check if it's an integrity error
                if isinstance(error_data, dict) and error_data.get("error") == "ChunkingIntegrityError":
                    raise SVOChunkingIntegrityError(
                        message=error.get("message", "Text integrity check failed"),
                        original_text_length=error_data.get("original_text_length"),
                        reconstructed_text_length=error_data.get("reconstructed_text_length"),
                        chunk_count=error_data.get("chunk_count"),
                        integrity_error=error_data.get("integrity_error"),
                        chunk_error=error,
                    )
                raise SVOServerError(
                    code=error.get("code", "job_failed"),
                    message=error.get("message", "Queued job failed"),
                    chunk_error=error,
                )

            result_payload = data.get("result", data)
            unwrapped = unwrap_result(result_payload)
            # Extract and return chunks as List[SemanticChunk]
            return extract_chunks_or_raise(unwrapped)

    async def chunk_text(
        self,
        text: str,
        verify_integrity: bool = False,
        **params: Any,
    ) -> List["SemanticChunk"]:
        """
        Chunk text into semantic chunks.

        Args:
            text: Text to chunk
            verify_integrity: If True, verify that chunks reconstruct the original text
            **params: Additional chunking parameters (type, language, window, etc.)

        Returns:
            List of SemanticChunk objects

        Raises:
            SVOChunkingIntegrityError: If verify_integrity=True and integrity check fails
            SVOServerError: If server returns an error
            SVOTimeoutError: If request times out
            SVOConnectionError: If connection fails
        """
        try:
            unified = await self._client.execute_command_unified(
                "chunk",
                {"text": text, **params},
                expect_queue=True,
                auto_poll=True,
                poll_interval=self.poll_interval,
                timeout=self.timeout if self.timeout is not None else None,
            )
        except Exception as exc:  # noqa: BLE001
            # Check if it's a JSON-RPC error with integrity error data
            if isinstance(exc, RuntimeError):
                error_str = str(exc).lower()
                if "integrity" in error_str:
                    # Try to extract error data from exception
                    error_data = getattr(exc, "data", {}) or {}
                    if isinstance(error_data, dict) and error_data.get("error") == "ChunkingIntegrityError":
                        raise SVOChunkingIntegrityError(
                            message=str(exc),
                            original_text_length=error_data.get("original_text_length"),
                            reconstructed_text_length=error_data.get("reconstructed_text_length"),
                            chunk_count=error_data.get("chunk_count"),
                            integrity_error=error_data.get("integrity_error"),
                        ) from exc
            raise map_exception(exc, self.timeout) from exc

        result = unwrap_result(unified)
        chunks = extract_chunks_or_raise(result)
        
        # Optional client-side integrity verification
        if verify_integrity:
            verify_text_integrity(chunks, text)
        
        return chunks

    async def get_help(self, cmdname: Optional[str] = None) -> Dict[str, Any]:
        """Get help info from chunker via JSON-RPC."""
        params = {"cmdname": cmdname} if cmdname else {}
        try:
            return await self._client.execute_command(
                "help", params, use_cmd_endpoint=False
            )
        except Exception as exc:  # noqa: BLE001
            raise map_exception(exc, self.timeout) from exc

    async def health(self) -> Dict[str, Any]:
        """Health check via JSON-RPC."""
        try:
            return await self._client.execute_command(
                "health", None, use_cmd_endpoint=False
            )
        except Exception as exc:  # noqa: BLE001
            raise map_exception(exc, self.timeout) from exc

    def reconstruct_text(self, chunks: List["SemanticChunk"]) -> str:
        """Reconstruct original text from SemanticChunk list.

        Args:
            chunks: List of SemanticChunk objects.

        Returns:
            Reconstructed text string.
        """
        return reconstruct_text(chunks)

    def verify_text_integrity(
        self, chunks: List["SemanticChunk"], original_text: str
    ) -> bool:
        """Verify that chunks reconstruct original text.

        Args:
            chunks: List of SemanticChunk objects.
            original_text: Original text that was chunked.

        Returns:
            True if integrity check passes.

        Raises:
            SVOChunkingIntegrityError: If chunks don't reconstruct original text.
        """
        return verify_text_integrity(chunks, original_text)

