"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

CLI for adapter-based ChunkerClient (queue-first).

Commands:
- health
- help
- chunk (one-shot: submit + wait)
- submit (enqueue only)
- status (single status fetch)
- logs (single logs fetch)
- wait (poll until completion)
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional

from svo_client.chunker_client import ChunkerClient, SVOServerError
from svo_client.config_loader import ConfigLoader
from svo_client.config_tools import ConfigGenerator, ConfigValidator


def _read_text(args: argparse.Namespace) -> str:
    """Read text from command line arguments or file.

    Args:
        args: Parsed command line arguments.

    Returns:
        Text content to chunk.

    Raises:
        SystemExit: If neither --text nor --file is provided.
    """
    if args.text:
        return args.text
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    raise SystemExit("❌ Provide --text or --file")


def _roles_from_arg(raw: Optional[str]) -> Optional[list[str]]:
    """Parse roles from comma-separated string.

    Args:
        raw: Comma-separated roles string or None.

    Returns:
        List of roles or None if empty.
    """
    if not raw:
        return None
    parts = [r.strip() for r in raw.split(",") if r.strip()]
    return parts or None


def _build_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Build client configuration from command line arguments.

    Priority: CLI args > env vars > config file

    Args:
        args: Parsed command line arguments.

    Returns:
        Configuration dictionary for ChunkerClient.

    Raises:
        SystemExit: If required arguments are missing.
    """
    # If config file is provided, load it as base
    config_file = getattr(args, "config", None)

    # If config file provided and no mode specified, use ConfigLoader.resolve_config
    if config_file and not args.mode:
        return ConfigLoader.resolve_config(
            host=args.host,
            port=args.port,
            cert=args.cert,
            key=args.key,
            ca=args.ca,
            token=args.token,
            token_header=args.token_header,
            check_hostname=args.check_hostname,
            timeout=args.timeout,
            config_file=config_file,
        )

    # Build config from CLI args with priority over env/config
    roles = _roles_from_arg(args.roles)
    mode = args.mode

    # Determine protocol and auth from mode
    mtls_modes = ("mtls", "mtls_token", "mtls_roles")
    token_modes = (
        "http_token", "http_token_roles",
        "https_token", "https_token_roles", "mtls_token"
    )
    use_mtls = mode in mtls_modes
    use_token = mode in token_modes

    # Validate required arguments
    if use_mtls:
        if not (args.cert and args.key and args.ca):
            raise SystemExit("❌ --cert, --key, --ca required for mtls modes")
    if use_token:
        if not args.token:
            raise SystemExit(f"❌ --token is required for {mode}")

    # Generate config based on mode
    # Use defaults if not provided
    host = args.host or "localhost"
    port = args.port or 8009
    if mode == "http":
        cfg = ConfigGenerator.http(host, port)
    elif mode in ("http_token", "http_token_roles"):
        cfg = ConfigGenerator.http_token(
            host, port, args.token, args.token_header, roles
        )
    elif mode == "https":
        cfg = ConfigGenerator.https(host, port, args.check_hostname)
    elif mode in ("https_token", "https_token_roles"):
        cfg = ConfigGenerator.https_token(
            host,
            port,
            args.token,
            args.token_header,
            roles,
            args.check_hostname,
        )
    elif mode in ("mtls", "mtls_roles"):
        cfg = ConfigGenerator.mtls(
            host,
            port,
            args.cert,
            args.key,
            args.ca,
            roles,
            args.check_hostname,
        )
    elif mode == "mtls_token":
        # mTLS with token: combine certificate auth with token
        cfg = ConfigGenerator.mtls(
            host,
            port,
            args.cert,
            args.key,
            args.ca,
            roles,
            args.check_hostname,
        )
        # Add token to mTLS config
        cfg["auth"]["method"] = "api_key"
        cfg["auth"]["header"] = args.token_header
        cfg["auth"]["api_keys"] = {"default": args.token}
        if roles:
            cfg["auth"]["roles"] = roles
    else:
        raise SystemExit(f"❌ Unsupported mode {mode}")

    # If config file provided, merge with CLI args (CLI has priority)
    if config_file:
        file_config = ConfigLoader.load_from_file(config_file)
        if file_config:
            # Merge: file config as base, CLI config overrides
            # If CLI config is empty (no mode specified), use file config as-is
            if not cfg or (not cfg.get("server") and not cfg.get("ssl") and not cfg.get("auth")):
                return ConfigValidator.validate(file_config)
            merged = ConfigLoader.merge_configs(file_config, cfg)
            return ConfigValidator.validate(merged)

    return ConfigValidator.validate(cfg)


async def cmd_health(args: argparse.Namespace) -> None:
    cfg = _build_config(args)
    async with ChunkerClient(
        config=cfg, timeout=args.timeout, poll_interval=args.poll_interval
    ) as client:
        result = await client.health()
        print(json.dumps(result, indent=2))


async def cmd_help(args: argparse.Namespace) -> None:
    cfg = _build_config(args)
    async with ChunkerClient(
        config=cfg, timeout=args.timeout, poll_interval=args.poll_interval
    ) as client:
        result = await client.get_help(args.command)
        print(json.dumps(result, indent=2))


async def cmd_chunk(args: argparse.Namespace) -> None:
    text = _read_text(args)
    cfg = _build_config(args)
    async with ChunkerClient(
        config=cfg, timeout=args.timeout, poll_interval=args.poll_interval
    ) as client:
        try:
            params = {"type": args.type}
            if args.language:
                params["language"] = args.language
            chunks = await client.chunk_text(text, **params)
            print(f"✅ chunks: {len(chunks)}")
            for idx, ch in enumerate(chunks[: args.max_print]):
                preview = ch.text[:120].replace("\n", " ")
                print(f"- #{idx} ({len(ch.text)} chars) {preview}")
        except SVOServerError as exc:
            print(f"❌ Server error {exc.code}: {exc.message}")
            if exc.chunk_error:
                print(json.dumps(exc.chunk_error, indent=2))


async def cmd_submit(args: argparse.Namespace) -> None:
    text = _read_text(args)
    cfg = _build_config(args)
    async with ChunkerClient(
        config=cfg, timeout=args.timeout, poll_interval=args.poll_interval
    ) as client:
        params = {"type": args.type}
        if args.language:
            params["language"] = args.language
        if args.role:
            params["role"] = args.role
        job_id = await client.submit_chunk_job(text, **params)
        print(json.dumps({"job_id": job_id, "status": "queued"}, indent=2))


async def cmd_status(args: argparse.Namespace) -> None:
    cfg = _build_config(args)
    async with ChunkerClient(
        config=cfg, timeout=args.timeout, poll_interval=args.poll_interval
    ) as client:
        status = await client.get_job_status(args.job_id)
        print(json.dumps(status, indent=2))


async def cmd_logs(args: argparse.Namespace) -> None:
    cfg = _build_config(args)
    async with ChunkerClient(
        config=cfg, timeout=args.timeout, poll_interval=args.poll_interval
    ) as client:
        logs = await client.get_job_logs(args.job_id)
        print(json.dumps(logs, indent=2))


async def cmd_wait(args: argparse.Namespace) -> None:
    cfg = _build_config(args)
    async with ChunkerClient(
        config=cfg, timeout=args.timeout, poll_interval=args.poll_interval
    ) as client:
        chunks = await client.wait_for_result(
            args.job_id,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
        )
        print(f"✅ chunks: {len(chunks)}")
        for idx, ch in enumerate(chunks[: args.max_print]):
            preview = ch.text[:120].replace("\n", " ")
            print(f"- #{idx} ({len(ch.text)} chars) {preview}")


async def cmd_list(args: argparse.Namespace) -> None:
    """List jobs in queue."""
    cfg = _build_config(args)
    async with ChunkerClient(
        config=cfg, timeout=args.timeout, poll_interval=args.poll_interval
    ) as client:
        jobs = await client.list_jobs(
            status=args.status,
            limit=args.limit,
        )
        print(json.dumps(jobs, indent=2))


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Adapter-based ChunkerClient CLI"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file (lowest priority)",
    )
    parser.add_argument(
        "--host",
        help="Server hostname (overrides env/config)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Server port (overrides env/config)",
    )
    parser.add_argument(
        "--mode",
        default="http",
        choices=[
            "http",
            "http_token",
            "http_token_roles",
            "https",
            "https_token",
            "https_token_roles",
            "mtls",
            "mtls_token",
            "mtls_roles",
        ],
        help="Connection mode / protocol",
    )
    parser.add_argument("--token-header", default="X-API-Key")
    parser.add_argument("--token", help="API token for *_token modes")
    parser.add_argument(
        "--roles",
        help="Comma-separated roles for *_roles modes",
    )
    parser.add_argument("--cert", help="Path to client certificate (mTLS)")
    parser.add_argument("--key", help="Path to client key (mTLS)")
    parser.add_argument("--ca", help="Path to CA certificate (mTLS)")
    parser.add_argument("--check-hostname", action="store_true")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Request timeout in seconds (default: no timeout)",
    )
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument(
        "--role",
        help="Optional role for chunk command payload",
    )

    sub = parser.add_subparsers(dest="action", required=True)

    p_health = sub.add_parser("health", help="Health check")
    p_health.set_defaults(func=cmd_health)

    p_help = sub.add_parser("help", help="Get help info")
    p_help.add_argument("--command")
    p_help.set_defaults(func=cmd_help)

    p_chunk = sub.add_parser("chunk", help="Chunk text")
    p_chunk.add_argument(
        "--text", help="Text to chunk"
    )
    p_chunk.add_argument(
        "--file", help="Path to file with text"
    )
    p_chunk.add_argument(
        "--language", help="Language code (optional, auto-detected if not specified)"
    )
    p_chunk.add_argument(
        "--type", default="Draft"
    )
    p_chunk.add_argument(
        "--max-print", type=int, default=5, help="Preview first N chunks"
    )
    p_chunk.set_defaults(func=cmd_chunk)

    p_submit = sub.add_parser("submit", help="Enqueue chunk job")
    p_submit.add_argument(
        "--text", help="Text to chunk"
    )
    p_submit.add_argument(
        "--file", help="Path to file with text"
    )
    p_submit.add_argument(
        "--language", help="Language code (optional, auto-detected if not specified)"
    )
    p_submit.add_argument(
        "--type", default="Draft"
    )
    p_submit.set_defaults(func=cmd_submit)

    p_status = sub.add_parser("status", help="Get job status")
    p_status.add_argument("job_id", help="Job identifier")
    p_status.set_defaults(func=cmd_status)

    p_logs = sub.add_parser("logs", help="Get job logs")
    p_logs.add_argument("job_id", help="Job identifier")
    p_logs.set_defaults(func=cmd_logs)

    p_wait = sub.add_parser("wait", help="Wait until job completes")
    p_wait.add_argument("job_id", help="Job identifier")
    p_wait.add_argument(
        "--max-print", type=int, default=5, help="Preview first N chunks"
    )
    p_wait.set_defaults(func=cmd_wait)

    p_list = sub.add_parser("list", help="List jobs in queue")
    p_list.add_argument(
        "--status",
        help="Filter by job status (e.g., queued, running, completed)",
    )
    p_list.add_argument(
        "--limit",
        type=int,
        help="Maximum number of jobs to return",
    )
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    """Main CLI entry point.

    Args:
        argv: Optional command line arguments. If None, uses sys.argv.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
