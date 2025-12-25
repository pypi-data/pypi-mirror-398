"""
Domain models describing UniProt artefacts exposed via MCP.

These Pydantic models provide the structured outputs returned by MCP tools.
The fields are intentionally stable even if upstream payloads evolve; any
unexpected data should be preserved through the `_raw` attribute on `Entry`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt


class Sequence(BaseModel):
    """Protein sequence with basic metadata."""

    length: NonNegativeInt = Field(description="Sequence length in amino acids.")
    value: str = Field(description="Primary amino acid sequence.")
    mol_weight: float | None = Field(
        default=None,
        description="Molecular weight in Daltons if reported by UniProt.",
    )
    crc64: str | None = Field(default=None, description="CRC64 checksum provided by UniProt.")


class GOAnnotation(BaseModel):
    """Gene Ontology annotation."""

    aspect: Literal["BP", "MF", "CC"] = Field(description="GO aspect code.")
    term: str = Field(description="Human-readable GO term.")
    id: str = Field(description="GO identifier (e.g. GO:0008150).")


class XRef(BaseModel):
    """Cross-reference entry in UniProt."""

    db: str = Field(description="Target database name.")
    id: str = Field(description="Identifier within the target database.")
    url: str | None = Field(
        default=None, description="Resolvable URL for the target record when available."
    )


class Feature(BaseModel):
    """Annotated protein feature (domains, variants, regions, etc.)."""

    type: str = Field(description="UniProt feature type.")
    start: int | None = Field(default=None, description="1-based start coordinate.")
    end: int | None = Field(default=None, description="1-based inclusive end coordinate.")
    description: str | None = Field(
        default=None, description="Free-text description provided by UniProt."
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Evidence codes supporting the feature.",
    )


class Entry(BaseModel):
    """Normalized UniProtKB entry."""

    model_config = ConfigDict(protected_namespaces=())

    accession: str = Field(description="Primary accession identifier.")
    id: str | None = Field(default=None, description="UniProt entry name/ID.")
    reviewed: bool = Field(description="True for Swiss-Prot, False for TrEMBL.")
    protein_name: str | None = Field(
        default=None, description="Recommended protein name where available."
    )
    gene_symbols: list[str] = Field(
        default_factory=list, description="Canonical gene symbols associated with the entry."
    )
    organism: str | None = Field(
        default=None, description="Scientific name of the source organism."
    )
    taxonomy_id: int | None = Field(
        default=None, description="NCBI taxonomy identifier for the organism."
    )
    sequence: Sequence | None = Field(
        default=None, description="Protein sequence metadata when available."
    )
    features: list[Feature] = Field(
        default_factory=list, description="Annotated sequence features."
    )
    go: list[GOAnnotation] = Field(
        default_factory=list, description="Gene Ontology annotations extracted from the entry."
    )
    xrefs: list[XRef] = Field(
        default_factory=list, description="Cross-references to external databases."
    )
    raw_payload: dict[str, object] | None = Field(
        default=None,
        description="Original UniProt payload for debugging or future enrichment.",
    )


class SearchHit(BaseModel):
    """Result entry returned by UniProt search endpoints."""

    accession: str = Field(description="Primary accession identifier.")
    id: str | None = Field(default=None, description="UniProt entry name/ID.")
    reviewed: bool = Field(description="True for Swiss-Prot hits.")
    protein_name: str | None = Field(
        default=None, description="Recommended protein name when available."
    )
    organism: str | None = Field(
        default=None, description="Scientific name of the source organism."
    )


class MappingResult(BaseModel):
    """Outcome of UniProt ID mapping operations."""

    from_db: str = Field(description="Source identifier namespace.")
    to_db: str = Field(description="Target identifier namespace.")
    results: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Mapping from input IDs to resolved identifiers (empty list for no match).",
    )
