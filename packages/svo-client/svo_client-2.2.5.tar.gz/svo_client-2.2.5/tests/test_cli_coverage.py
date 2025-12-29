"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests to increase CLI coverage.
"""

import argparse
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from svo_client.cli import (
    _build_config,
    _read_text,
    _roles_from_arg,
    build_parser,
    cmd_chunk,
    cmd_health,
    cmd_help,
    cmd_list,
    cmd_logs,
    cmd_status,
    cmd_submit,
    cmd_wait,
    main,
)


class TestCLICoverage:
    """Tests to increase CLI coverage."""

    def test_read_text_from_args(self):
        """Test _read_text with --text argument."""
        args = argparse.Namespace(text="Test text", file=None)
        result = _read_text(args)
        assert result == "Test text"

    def test_read_text_from_file(self):
        """Test _read_text with --file argument."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt"
        ) as f:
            f.write("File content")
            file_path = f.name

        try:
            args = argparse.Namespace(text=None, file=file_path)
            result = _read_text(args)
            assert result == "File content"
        finally:
            Path(file_path).unlink()

    def test_read_text_missing(self):
        """Test _read_text with no arguments."""
        args = argparse.Namespace(text=None, file=None)
        with pytest.raises(SystemExit):
            _read_text(args)

    def test_roles_from_arg_comma_separated(self):
        """Test _roles_from_arg with comma-separated roles."""
        assert _roles_from_arg("admin,user") == ["admin", "user"]
        assert _roles_from_arg("admin, user, reader") == [
            "admin",
            "user",
            "reader",
        ]

    def test_roles_from_arg_empty(self):
        """Test _roles_from_arg with empty values."""
        assert _roles_from_arg(None) is None
        assert _roles_from_arg("") is None
        assert _roles_from_arg("  ") is None

    @pytest.mark.asyncio
    async def test_cmd_health(self):
        """Test cmd_health function."""
        args = argparse.Namespace(
            mode="http",
            host="localhost",
            port=8009,
            token=None,
            token_header="X-API-Key",
            roles=None,
            cert=None,
            key=None,
            ca=None,
            check_hostname=False,
            timeout=None,
            poll_interval=1.0,
            config=None,
        )

        with patch("svo_client.cli.ChunkerClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.health = AsyncMock(return_value={"status": "ok"})
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await cmd_health(args)
            mock_client.health.assert_called_once()

    @pytest.mark.asyncio
    async def test_cmd_help(self):
        """Test cmd_help function."""
        args = argparse.Namespace(
            mode="http",
            host="localhost",
            port=8009,
            token=None,
            token_header="X-API-Key",
            roles=None,
            cert=None,
            key=None,
            ca=None,
            check_hostname=False,
            timeout=None,
            poll_interval=1.0,
            config=None,
            command=None,
        )

        with patch("svo_client.cli.ChunkerClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_help = AsyncMock(
                return_value={"help": "test"}
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await cmd_help(args)
            mock_client.get_help.assert_called_once()

    @pytest.mark.asyncio
    async def test_cmd_chunk(self):
        """Test cmd_chunk function."""
        args = argparse.Namespace(
            mode="http",
            host="localhost",
            port=8009,
            token=None,
            token_header="X-API-Key",
            roles=None,
            cert=None,
            key=None,
            ca=None,
            check_hostname=False,
            timeout=None,
            poll_interval=1.0,
            config=None,
            text="Test text",
            file=None,
            language="en",
            type="Draft",
            max_print=5,
        )

        with patch("svo_client.cli.ChunkerClient") as mock_client_class:
            from chunk_metadata_adapter import SemanticChunk

            mock_chunks = [
                SemanticChunk(
                    text="Test",
                    ordinal=0,
                    type="Draft",
                    body="Test",
                )
            ]
            mock_client = AsyncMock()
            mock_client.chunk_text = AsyncMock(return_value=mock_chunks)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await cmd_chunk(args)
            mock_client.chunk_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_cmd_submit(self):
        """Test cmd_submit function."""
        args = argparse.Namespace(
            mode="http",
            host="localhost",
            port=8009,
            token=None,
            token_header="X-API-Key",
            roles=None,
            cert=None,
            key=None,
            ca=None,
            check_hostname=False,
            timeout=None,
            poll_interval=1.0,
            config=None,
            text="Test text",
            file=None,
            language="en",
            type="Draft",
            role=None,
        )

        with patch("svo_client.cli.ChunkerClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.submit_chunk_job = AsyncMock(
                return_value="job-123"
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await cmd_submit(args)
            mock_client.submit_chunk_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_cmd_status(self):
        """Test cmd_status function."""
        args = argparse.Namespace(
            mode="http",
            host="localhost",
            port=8009,
            token=None,
            token_header="X-API-Key",
            roles=None,
            cert=None,
            key=None,
            ca=None,
            check_hostname=False,
            timeout=None,
            poll_interval=1.0,
            config=None,
            job_id="job-123",
        )

        with patch("svo_client.cli.ChunkerClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_job_status = AsyncMock(
                return_value={"status": "completed"}
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await cmd_status(args)
            mock_client.get_job_status.assert_called_once_with("job-123")

    @pytest.mark.asyncio
    async def test_cmd_logs(self):
        """Test cmd_logs function."""
        args = argparse.Namespace(
            mode="http",
            host="localhost",
            port=8009,
            token=None,
            token_header="X-API-Key",
            roles=None,
            cert=None,
            key=None,
            ca=None,
            check_hostname=False,
            timeout=None,
            poll_interval=1.0,
            config=None,
            job_id="job-123",
        )

        with patch("svo_client.cli.ChunkerClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_job_logs = AsyncMock(return_value={"logs": []})
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await cmd_logs(args)
            mock_client.get_job_logs.assert_called_once_with("job-123")

    @pytest.mark.asyncio
    async def test_cmd_wait(self):
        """Test cmd_wait function."""
        args = argparse.Namespace(
            mode="http",
            host="localhost",
            port=8009,
            token=None,
            token_header="X-API-Key",
            roles=None,
            cert=None,
            key=None,
            ca=None,
            check_hostname=False,
            timeout=None,
            poll_interval=1.0,
            config=None,
            job_id="job-123",
        )

        with patch("svo_client.cli.ChunkerClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.wait_for_result = AsyncMock(
                return_value={"result": "done"}
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await cmd_wait(args)
            mock_client.wait_for_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_cmd_list(self):
        """Test cmd_list function."""
        args = argparse.Namespace(
            mode="http",
            host="localhost",
            port=8009,
            token=None,
            token_header="X-API-Key",
            roles=None,
            cert=None,
            key=None,
            ca=None,
            check_hostname=False,
            timeout=None,
            poll_interval=1.0,
            config=None,
            status=None,
            limit=None,
        )

        with patch("svo_client.cli.ChunkerClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.list_jobs = AsyncMock(return_value=[])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await cmd_list(args)
            mock_client.list_jobs.assert_called_once()

    def test_build_parser(self):
        """Test build_parser function."""
        parser = build_parser()
        assert parser is not None
        assert parser.prog is not None

    def test_main(self):
        """Test main function."""
        with patch("svo_client.cli.build_parser") as mock_parser:
            mock_args = MagicMock()
            mock_args.func = AsyncMock()
            mock_parser.return_value.parse_args.return_value = mock_args

            with patch("asyncio.run") as mock_run:
                main(["health"])
                mock_run.assert_called_once()

