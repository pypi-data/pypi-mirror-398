"""
Observability utilities: structured logging, request correlation, and HTTP hooks.
"""

from __future__ import annotations

import contextvars
import json
import logging
import os
import time
import uuid
from collections.abc import Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# -----------------------------------------------------------------------------
# Request correlation
# -----------------------------------------------------------------------------

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "uniprot_mcp_request_id", default=None
)


def get_request_id() -> str | None:
    """Return the current request id if one is set."""

    return request_id_var.get()


# -----------------------------------------------------------------------------
# Structured logging
# -----------------------------------------------------------------------------

_RESERVED = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}


class JsonFormatter(logging.Formatter):
    """Minimal JSON formatter with request id propagation."""

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        req_id = get_request_id()
        if req_id:
            data["request_id"] = req_id
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_") and key not in data:
                data[key] = value
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


def configure_logging(
    level: str | None = None,
    fmt: str | None = None,
    *,
    root_logger: str = "uniprot_mcp",
) -> None:
    """
    Configure application logging.

    Environment overrides:
        UNIPROT_LOG_LEVEL: debug|info|warning|error (default: info)
        UNIPROT_LOG_FORMAT: plain|json (default: plain)
    """

    resolved_level = (level or os.getenv("UNIPROT_LOG_LEVEL") or "info").upper()
    resolved_fmt = (fmt or os.getenv("UNIPROT_LOG_FORMAT") or "plain").lower()

    root = logging.getLogger()
    root.setLevel(getattr(logging, resolved_level, logging.INFO))

    # Avoid duplicate handlers across reloads.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    if resolved_fmt == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(name)s [req=%(request_id)s] %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
    root.addHandler(handler)

    # Ensure project loggers inherit the same level.
    logging.getLogger(root_logger).setLevel(getattr(logging, resolved_level, logging.INFO))
    logging.getLogger("starlette").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


# -----------------------------------------------------------------------------
# Starlette middleware
# -----------------------------------------------------------------------------


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach (or propagate) X-Request-ID headers for each HTTP request."""

    def __init__(self, app, header_name: str = "X-Request-ID") -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(self.header_name) or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers.setdefault(self.header_name, request_id)
        return response


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Log HTTP access details (method, path, latency, status)."""

    def __init__(self, app) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.log = logging.getLogger("uniprot_mcp.access")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
            self.log.info(
                "http_access",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": status,
                    "duration_ms": duration_ms,
                    "request_id": get_request_id(),
                },
            )


# -----------------------------------------------------------------------------
# HTTPX event hooks
# -----------------------------------------------------------------------------


def create_httpx_event_hooks(
    logger: logging.Logger | None = None,
) -> dict[str, list[Callable[[Any], None]]]:
    """Return HTTPX event hooks logging duration and status."""

    log = logger or logging.getLogger("uniprot_mcp.httpx")

    def on_request(request: Any) -> None:
        request.extensions["start_ts"] = time.perf_counter()

    def on_response(response: Any) -> None:
        start = response.request.extensions.get("start_ts")
        duration_ms = None
        if start is not None:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
        log.info(
            "httpx_request",
            extra={
                "method": response.request.method,
                "url": str(response.request.url),
                "status": response.status_code,
                "duration_ms": duration_ms,
                "request_id": get_request_id(),
            },
        )

    return {"request": [on_request], "response": [on_response]}


__all__ = [
    "AccessLogMiddleware",
    "JsonFormatter",
    "RequestIdMiddleware",
    "configure_logging",
    "create_httpx_event_hooks",
    "get_request_id",
]
