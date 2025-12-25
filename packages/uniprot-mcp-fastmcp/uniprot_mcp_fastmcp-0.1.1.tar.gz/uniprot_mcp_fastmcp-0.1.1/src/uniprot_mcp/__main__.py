"""
Command-line helpers for running the UniProt MCP server.

This module exposes the entry point used by the ``uniprot-mcp-http`` script
defined in ``pyproject.toml``. Environment variables can be used to override
the bind host/port without changing the invocation:

* ``MCP_HTTP_HOST`` (default: ``0.0.0.0``)
* ``MCP_HTTP_PORT`` (default: ``8000``)
* ``MCP_HTTP_LOG_LEVEL`` (default: ``info``)
* ``MCP_HTTP_RELOAD`` (default: ``0`` disables auto-reload)
"""

from __future__ import annotations

import argparse
import os
from typing import Final

import uvicorn

DEFAULT_HOST: Final[str] = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
DEFAULT_PORT: Final[int] = int(os.getenv("MCP_HTTP_PORT", "8000"))
DEFAULT_LOG_LEVEL: Final[str] = os.getenv("MCP_HTTP_LOG_LEVEL", "info")
DEFAULT_RELOAD: Final[bool] = os.getenv("MCP_HTTP_RELOAD", "").lower() in {"1", "true", "yes"}


def run_http() -> None:
    """Run the streamable HTTP server using uvicorn."""

    parser = argparse.ArgumentParser(description="Run the UniProt MCP HTTP server.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host interface to bind")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port to bind",
    )
    parser.add_argument(
        "--log-level",
        default=DEFAULT_LOG_LEVEL,
        help="Uvicorn log level (debug, info, warning, error)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=DEFAULT_RELOAD,
        help="Enable auto-reload on code changes (development only)",
    )
    args = parser.parse_args()

    uvicorn.run(
        "uniprot_mcp.http_app:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload,
    )


if __name__ == "__main__":
    run_http()
