"""
Prompt registration utilities.

Prompts are kept in a dedicated module so they can be reused by additional
transports (e.g., streamable HTTP) without circular imports.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base


def register_prompts(mcp: FastMCP) -> None:
    """Register UniProt prompts with the given MCP server instance."""

    @mcp.prompt(title="Summarize Protein")  # type: ignore[misc]
    def summarize_protein(
        accession: str,
        include_organism: bool = True,
        include_go: bool = True,
        include_features: bool = False,
    ) -> list[base.Message]:
        """Generate instructions for summarising a UniProt entry."""

        bullet_points = [
            f"Summarize the protein entry with accession {accession}.",
            "Audience is a non-specialist developer integrating UniProt data into an agent.",
            "Highlight reviewed status and key functional roles.",
        ]
        if include_organism:
            bullet_points.append("Identify the source organism and taxonomy ID if present.")
        if include_go:
            bullet_points.append("Summarize GO annotations grouped by BP/MF/CC.")
        if include_features:
            bullet_points.append("Call out significant sequence features (domains, variants).")
        bullet_points.append("Cite UniProt where applicable.")

        prompt_text = "\n- ".join(["Please prepare the following summary:"] + bullet_points)
        return [base.UserMessage(prompt_text)]
