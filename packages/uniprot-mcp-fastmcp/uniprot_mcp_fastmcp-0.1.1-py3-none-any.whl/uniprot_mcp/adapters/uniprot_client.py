"""
Async client helpers for interacting with the UniProt REST API.

These helpers expose thin wrappers around `httpx.AsyncClient` with retry-aware
behaviour via Tenacity. More advanced configuration (proxy support, etc.) can
be layered later without touching the rest of the server.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Iterable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, cast

import httpx
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from uniprot_mcp.obs import create_httpx_event_hooks

DEFAULT_BASE_URL = "https://rest.uniprot.org"
DEFAULT_TIMEOUT = 20.0  # seconds
USER_AGENT = "uniprot-mcp/0.1"

FIELDS_SEQUENCE_MIN = "accession,sequence"
FIELDS_SEARCH_LIGHT = "accession,protein_name,organism_name,entry_type"
FLATFILE_ACCEPT = {
    "txt": "text/plain;format=txt",
    "fasta": "text/plain;format=fasta",
}

RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}

MAX_CONCURRENCY = max(1, int(os.getenv("UNIPROT_MAX_CONCURRENCY", "8")))
_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENCY)


class UniProtClientError(RuntimeError):
    """Raised when UniProt returns an unrecoverable error."""


def _should_retry(exc: BaseException) -> bool:
    """Return True for network errors that should be retried."""
    if isinstance(exc, httpx.RequestError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS
    return False


def _before_sleep(retry_state: RetryCallState) -> None:
    """Hook for debugging retry behaviour."""
    # Placeholder for future logging (avoid importing logging until needed).
    return


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if value.isdigit():
        try:
            return max(0.0, float(int(value)))
        except ValueError:
            return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        now = datetime.now(UTC)
        return max(0.0, (parsed - now).total_seconds())
    except (TypeError, ValueError):
        return None


_BACKOFF = wait_random_exponential(multiplier=0.6, max=6.0)


def _wait_retry_after_or_exponential(retry_state: RetryCallState) -> float:
    """Respect Retry-After headers on 429s, fall back to exponential jitter."""

    exc = retry_state.outcome.exception() if retry_state.outcome else None
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
        retry_after = _parse_retry_after(exc.response.headers.get("Retry-After"))
        if retry_after and retry_after > 0.0:
            return float(min(retry_after, 30.0))
    return float(_BACKOFF(retry_state))


def new_client(
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout: httpx.Timeout | float = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
) -> httpx.AsyncClient:
    """Return a configured AsyncClient for UniProt requests."""

    merged_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if headers:
        merged_headers.update(headers)

    if isinstance(timeout, (int, float)):
        resolved_timeout = httpx.Timeout(connect=5.0, read=timeout, write=timeout, pool=5.0)
    else:
        resolved_timeout = timeout

    return httpx.AsyncClient(
        base_url=base_url,
        headers=merged_headers,
        timeout=resolved_timeout,
        follow_redirects=True,
        trust_env=True,
        event_hooks=create_httpx_event_hooks(),
    )


def _ensure_dict(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    raise UniProtClientError("UniProt response did not contain a JSON object.")


@retry(  # type: ignore[misc]
    reraise=True,
    stop=stop_after_attempt(4),
    wait=_wait_retry_after_or_exponential,
    retry=retry_if_exception(_should_retry),
    before_sleep=_before_sleep,
)
async def fetch_entry_json(
    client: httpx.AsyncClient,
    accession: str,
    *,
    fields: Iterable[str] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    """Return the UniProt entry payload for the provided accession."""

    params: dict[str, Any] = {}
    if fields:
        params["fields"] = ",".join(fields)
    if version:
        params["version"] = version

    async with _SEMAPHORE:
        response = await client.get(
            f"/uniprotkb/{accession}",
            params=params or None,
        )
    if response.status_code == 404:
        return {}
    if response.status_code == 204:
        return {}
    if response.status_code >= 400:
        if response.status_code in RETRYABLE_STATUS:
            response.raise_for_status()
        else:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise UniProtClientError(str(exc)) from exc
    return _ensure_dict(response.json())


@retry(  # type: ignore[misc]
    reraise=True,
    stop=stop_after_attempt(4),
    wait=_wait_retry_after_or_exponential,
    retry=retry_if_exception(_should_retry),
    before_sleep=_before_sleep,
)
async def fetch_entry_flatfile(
    client: httpx.AsyncClient,
    accession: str,
    version: str,
    *,
    format: str = "txt",
) -> str:
    """Return a flatfile representation (txt or fasta) for a specific entry version."""

    normalized_format = format.lower()
    if normalized_format not in FLATFILE_ACCEPT:
        raise ValueError("format must be 'txt' or 'fasta'")

    headers = {"Accept": FLATFILE_ACCEPT[normalized_format]}
    params = {"version": version, "format": normalized_format}

    async with _SEMAPHORE:
        response = await client.get(
            f"/uniprotkb/{accession}",
            params=params,
            headers=headers,
        )
    if response.status_code == 404:
        return ""
    if response.status_code >= 400:
        if response.status_code in RETRYABLE_STATUS:
            response.raise_for_status()
        else:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise UniProtClientError(str(exc)) from exc
    return cast(str, response.text)


@retry(  # type: ignore[misc]
    reraise=True,
    stop=stop_after_attempt(4),
    wait=_wait_retry_after_or_exponential,
    retry=retry_if_exception(_should_retry),
    before_sleep=_before_sleep,
)
async def fetch_sequence_json(client: httpx.AsyncClient, accession: str) -> dict[str, Any]:
    """Fetch only the minimal fields required for sequence metadata."""

    params = None
    if os.getenv("UNIPROT_ENABLE_FIELDS"):
        params = {"fields": FIELDS_SEQUENCE_MIN}
    async with _SEMAPHORE:
        response = await client.get(f"/uniprotkb/{accession}", params=params)
    if response.status_code == 404:
        return {}
    if response.status_code >= 400:
        if response.status_code in RETRYABLE_STATUS:
            response.raise_for_status()
        else:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise UniProtClientError(str(exc)) from exc
    return _ensure_dict(response.json())


@retry(  # type: ignore[misc]
    reraise=True,
    stop=stop_after_attempt(4),
    wait=_wait_retry_after_or_exponential,
    retry=retry_if_exception(_should_retry),
    before_sleep=_before_sleep,
)
async def search_json(
    client: httpx.AsyncClient,
    *,
    query: str,
    size: int,
    reviewed_only: bool = False,
    fields: Iterable[str] | None = None,
    sort: str | None = None,
    include_isoform: bool | None = None,
) -> dict[str, Any]:
    """Search UniProtKB and return the raw JSON response."""

    actual_query = query
    if reviewed_only and "reviewed:" not in query.lower():
        actual_query = f"({query}) AND reviewed:true"

    bounded_size = max(1, min(size, 500))

    params: dict[str, Any] = {
        "query": actual_query,
        "size": bounded_size,
    }
    if fields:
        params["fields"] = ",".join(fields)
    if sort:
        params["sort"] = sort
    if include_isoform is not None:
        params["includeIsoform"] = str(include_isoform).lower()

    async with _SEMAPHORE:
        response = await client.get(
            "/uniprotkb/search",
            params=params,
        )
    if response.status_code >= 400:
        if response.status_code in RETRYABLE_STATUS:
            response.raise_for_status()
        else:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise UniProtClientError(str(exc)) from exc
    return _ensure_dict(response.json())


@retry(  # type: ignore[misc]
    reraise=True,
    stop=stop_after_attempt(4),
    wait=_wait_retry_after_or_exponential,
    retry=retry_if_exception(_should_retry),
    before_sleep=_before_sleep,
)
async def start_id_mapping(
    client: httpx.AsyncClient,
    *,
    from_db: str,
    to_db: str,
    ids: Iterable[str],
) -> str:
    """Submit an ID mapping job and return its job identifier."""

    async with _SEMAPHORE:
        response = await client.post(
            "/idmapping/run",
            data={
                "from": from_db,
                "to": to_db,
                "ids": ",".join(ids),
            },
        )
    if response.status_code >= 400:
        if response.status_code in RETRYABLE_STATUS:
            response.raise_for_status()
        else:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise UniProtClientError(str(exc)) from exc

    payload = _ensure_dict(response.json())
    job_id = payload.get("jobId") or payload.get("job", {}).get("jobId")
    if not job_id:
        raise UniProtClientError("ID mapping response missing job identifier.")
    return str(job_id)


@retry(  # type: ignore[misc]
    reraise=True,
    stop=stop_after_attempt(4),
    wait=_wait_retry_after_or_exponential,
    retry=retry_if_exception(_should_retry),
    before_sleep=_before_sleep,
)
async def get_mapping_status(client: httpx.AsyncClient, job_id: str) -> dict[str, Any]:
    """Return the current status for a mapping job."""

    async with _SEMAPHORE:
        response = await client.get(f"/idmapping/status/{job_id}")
    if response.status_code >= 400:
        if response.status_code in RETRYABLE_STATUS:
            response.raise_for_status()
        else:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise UniProtClientError(str(exc)) from exc
    return _ensure_dict(response.json())


@retry(  # type: ignore[misc]
    reraise=True,
    stop=stop_after_attempt(4),
    wait=_wait_retry_after_or_exponential,
    retry=retry_if_exception(_should_retry),
    before_sleep=_before_sleep,
)
async def get_mapping_results(client: httpx.AsyncClient, job_id: str) -> dict[str, Any]:
    """Return the mapping results for a completed job."""

    async with _SEMAPHORE:
        response = await client.get(
            f"/idmapping/results/{job_id}",
            params={"format": "json"},
        )
    if response.status_code >= 400:
        if response.status_code in RETRYABLE_STATUS:
            response.raise_for_status()
        else:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise UniProtClientError(str(exc)) from exc
    return _ensure_dict(response.json())
