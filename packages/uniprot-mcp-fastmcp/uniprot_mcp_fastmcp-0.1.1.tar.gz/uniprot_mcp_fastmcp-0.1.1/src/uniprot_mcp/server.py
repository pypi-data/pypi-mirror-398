"""
FastMCP stdio server entry point exposing UniProt data.

The server is intentionally focused on the stdio transport for M1. Streamable
HTTP wiring will be introduced in later milestones.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from collections.abc import Iterable
from typing import Any, cast

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

from uniprot_mcp.adapters.parsers import (
    parse_entry,
    parse_mapping_result,
    parse_search_hits,
    parse_sequence_from_entry,
)
from uniprot_mcp.adapters.uniprot_client import (
    FIELDS_SEARCH_LIGHT,
    UniProtClientError,
    fetch_entry_json,
    fetch_sequence_json,
    get_mapping_results,
    get_mapping_status,
    new_client,
    search_json,
    start_id_mapping,
)
from uniprot_mcp.adapters.uniprot_client import (
    fetch_entry_flatfile as fetch_entry_flatfile_raw,
)
from uniprot_mcp.models.domain import Entry, MappingResult, SearchHit, Sequence
from uniprot_mcp.prompts import register_prompts

INSTRUCTIONS = (
    "Read-only UniProtKB access: fetch entries, sequences, curated search results, "
    "and identifier mappings."
)
RESOURCE_NOT_FOUND_MESSAGE = "No UniProt entry found for accession '{accession}'."
MAPPING_POLL_INTERVAL = 0.75
MAPPING_MAX_WAIT = 30.0
ACCESSION_PATTERN = re.compile(
    r"([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z]([0-9][A-Z][A-Z0-9]{2}){1,2}[0-9])(((-[0-9]{1,3})?(\[\d+-\d+\])?)|(\.[0-9]{1,3})|(_[A-Z0-9]{2,5}))?|[A-Z0-9]{2,5}_[A-Z0-9]{2,5}"
)

mcp = FastMCP(
    name="UniProt MCP",
    instructions=INSTRUCTIONS,
    website_url="https://www.uniprot.org",
)

register_prompts(mcp)


def _validate_accession(accession: str) -> str:
    candidate = accession.strip().upper()
    if not ACCESSION_PATTERN.fullmatch(candidate):
        raise ValueError(f"Invalid UniProt accession: {accession}")
    return candidate


async def _load_entry(
    accession: str,
    *,
    fields: Iterable[str] | None = None,
) -> tuple[str, dict[str, Any]]:
    normalized = _validate_accession(accession)
    async with new_client() as client:
        payload = await fetch_entry_json(client, normalized, fields=fields)
    return normalized, cast(dict[str, Any], payload)


@mcp.resource("uniprot://uniprotkb/{accession}")  # type: ignore[misc]
async def entry_resource(accession: str) -> str:
    """Return the raw UniProt entry JSON payload for context stuffing."""

    normalized, payload = await _load_entry(accession)
    if not payload:
        return RESOURCE_NOT_FOUND_MESSAGE.format(accession=normalized)
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


@mcp.resource("uniprot://help/search")  # type: ignore[misc]
def search_help() -> str:
    """Static help text explaining search conventions."""

    return (
        "UniProtKB search help:\n"
        "- Use search_uniprot(query, size, reviewed_only, fields, sort, include_isoform)\n"
        "  to retrieve curated hits.\n"
        "- Examples:\n"
        '    query="P53 AND organism:9606", reviewed_only=True\n'
        '    query="kinase AND taxonomy:9606"\n'
        "- Optional arguments: fields (list[str]), sort (string), include_isoform (bool).\n"
        "- The tool caps 'size' at 500 results to keep responses manageable."
    )


@mcp.tool()  # type: ignore[misc]
async def fetch_entry(
    accession: str,
    fields: list[str] | None = None,
    version: str | None = None,
) -> Entry:
    """Return a structured UniProt entry."""

    if version is not None:
        raise ValueError(
            "Versioned entries are only available as flatfiles. "
            "Use fetch_entry_flatfile(accession, version) for historical versions."
        )
    normalized, payload = await _load_entry(accession, fields=fields)
    if not payload:
        return Entry(
            accession=normalized,
            reviewed=False,
            gene_symbols=[],
            features=[],
            go=[],
            xrefs=[],
        )
    return parse_entry(payload)


@mcp.tool()  # type: ignore[misc]
async def get_sequence(accession: str) -> Sequence | None:
    """Return only the sequence metadata for an accession."""

    normalized = _validate_accession(accession)
    async with new_client() as client:
        payload = await fetch_sequence_json(client, normalized)
    if not payload:
        return None
    return parse_sequence_from_entry(payload)


@mcp.tool()  # type: ignore[misc]
async def search_uniprot(
    query: str,
    size: int = 10,
    reviewed_only: bool = False,
    fields: list[str] | None = None,
    sort: str | None = None,
    include_isoform: bool = False,
) -> list[SearchHit]:
    """Search UniProtKB and return curated hits."""

    size = max(1, min(size, 500))
    effective_fields = fields
    if fields is None and os.getenv("UNIPROT_ENABLE_FIELDS"):
        effective_fields = [FIELDS_SEARCH_LIGHT]
    async with new_client() as client:
        payload = await search_json(
            client,
            query=query,
            size=size,
            reviewed_only=reviewed_only,
            fields=effective_fields,
            sort=sort,
            include_isoform=include_isoform,
        )
    return parse_search_hits(payload)


@mcp.tool()  # type: ignore[misc]
async def fetch_entry_flatfile(
    accession: str,
    version: str,
    format: str = "txt",
) -> str:
    """Return the UniProt flatfile (txt or fasta) for a specific entry version."""

    normalized = _validate_accession(accession)
    normalized_format = format.lower()
    async with new_client() as client:
        text = cast(
            str,
            await fetch_entry_flatfile_raw(
                client,
                normalized,
                version,
                format=normalized_format,
            ),
        )
    if not text:
        return RESOURCE_NOT_FOUND_MESSAGE.format(accession=normalized)
    return text


async def _poll_mapping_job(
    job_id: str,
    *,
    ctx: Context[ServerSession, None] | None = None,
) -> dict[str, Any]:
    """Poll the UniProt mapping job until completion or timeout."""

    elapsed = 0.0
    async with new_client() as client:
        while elapsed < MAPPING_MAX_WAIT:
            status = await get_mapping_status(client, job_id)
            if _mapping_is_complete(status):
                results = await get_mapping_results(client, job_id)
                return cast(dict[str, Any], results)
            elapsed += MAPPING_POLL_INTERVAL
            if ctx is not None:
                progress = min(1.0, elapsed / MAPPING_MAX_WAIT)
                await ctx.report_progress(
                    progress=progress,
                    total=1.0,
                    message="Polling UniProt ID mapping job",
                )
            await asyncio.sleep(MAPPING_POLL_INTERVAL)
        raise UniProtClientError("ID mapping timed out waiting for completion.")


def _mapping_is_complete(status: dict[str, Any]) -> bool:
    """Determine whether a mapping job has completed."""

    complete_flags = {
        "FINISHED",
        "FINISHED_UNSUCCESSFULLY",
        "COMPLETE",
        "COMPLETED",
        "DONE",
    }
    failed_flags = {"FAILED", "ERROR", "CANCELLED"}
    if status.get("status") in failed_flags or status.get("jobStatus") in failed_flags:
        raise UniProtClientError(f"ID mapping failed with status: {status}")
    if status.get("status") in complete_flags:
        return True
    if status.get("jobStatus") in complete_flags:
        return True
    return bool(status.get("resultsReady") or status.get("ready"))


@mcp.tool()  # type: ignore[misc]
async def map_ids(
    from_db: str,
    to_db: str,
    ids: list[str],
    ctx: Context[ServerSession, None] | None = None,
) -> MappingResult:
    """Map identifiers between UniProt-supported namespaces."""

    filtered_ids = [identifier for identifier in ids if identifier]
    if not filtered_ids:
        return MappingResult(from_db=from_db, to_db=to_db, results={})

    async with new_client() as client:
        job_id = await start_id_mapping(client, from_db=from_db, to_db=to_db, ids=filtered_ids)

    if ctx is not None:
        await ctx.info(
            f"Submitted UniProt ID mapping job ({from_db}->{to_db}) for {len(filtered_ids)} IDs."
        )

    payload = await _poll_mapping_job(job_id, ctx=ctx)
    if ctx is not None:
        await ctx.info(
            f"Completed UniProt ID mapping job ({from_db}->{to_db}) for {len(filtered_ids)} IDs."
        )
    return parse_mapping_result(payload, from_db=from_db, to_db=to_db)


def main() -> None:
    """Run the stdio server."""

    mcp.run()


if __name__ == "__main__":
    main()
