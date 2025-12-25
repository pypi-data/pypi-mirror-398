# src/uniprot_mcp/http_app.py
"""
Starlette application exposing the FastMCP server over streamable HTTP.

This module wires the M1 stdio implementation into an HTTP transport with
browser-friendly CORS defaults. The server mounts the MCP endpoint at `/mcp`
and provides a `/healthz` endpoint for readiness checks.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterable
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from uniprot_mcp.obs import AccessLogMiddleware, RequestIdMiddleware, configure_logging
from uniprot_mcp.server import mcp

HEALTH_PATH = "/healthz"
MCP_MOUNT_PATH = "/mcp"
DEFAULT_ALLOWED_METHODS = ["GET", "POST", "DELETE"]
EXPOSED_HEADERS = ["Mcp-Session-Id", "X-Request-Id"]


def _parse_origins(value: str | None) -> list[str]:
    if not value:
        return ["*"]
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def _cors_allow_headers() -> Iterable[str]:
    value = os.getenv("MCP_CORS_ALLOW_HEADERS")
    if value:
        return [header.strip() for header in value.split(",") if header.strip()]
    # Allow all headers by default; tighten via env if needed.
    return ["*"]


def _create_app() -> Starlette:
    """Create the Starlette application with CORS and health check."""

    configure_logging()

    # Ensure the MCP ASGI app mounts cleanly under /mcp.
    mcp.settings.streamable_http_path = "/"
    mcp_app = mcp.streamable_http_app()

    async def health_check(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    metrics_route: Route | None = None
    try:
        import prometheus_client as prom  # type: ignore[import-not-found]

        async def metrics(_request: Request) -> Response:
            content = prom.generate_latest()
            return Response(
                content,
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )

        metrics_route = Route("/metrics", endpoint=metrics)
    except Exception:  # pragma: no cover - optional dependency
        metrics_route = None

    @asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        async with mcp.session_manager.run():
            yield

    routes = [
        Route(HEALTH_PATH, endpoint=health_check),
        Mount(MCP_MOUNT_PATH, app=mcp_app),
    ]
    if metrics_route is not None:
        routes.append(metrics_route)

    starlette_app = Starlette(
        routes=routes,
        lifespan=lifespan,
    )

    allow_origins = _parse_origins(os.getenv("MCP_CORS_ALLOW_ORIGINS"))
    allow_methods = os.getenv("MCP_CORS_ALLOW_METHODS")
    methods = (
        [method.strip() for method in allow_methods.split(",") if method.strip()]
        if allow_methods
        else DEFAULT_ALLOWED_METHODS
    )

    starlette_app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_methods=methods,
        allow_headers=list(_cors_allow_headers()),
        expose_headers=EXPOSED_HEADERS,
    )
    starlette_app.add_middleware(RequestIdMiddleware)
    starlette_app.add_middleware(AccessLogMiddleware)
    return starlette_app


app = _create_app()


__all__ = ["app"]
