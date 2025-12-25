"""
Parsing helpers converting UniProt responses into domain models.

The UniProt REST responses contain many nested objects; these helpers strip the
payloads down to stable, server-owned data classes defined in
`uniprot_mcp.models.domain`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from uniprot_mcp.models.domain import (
    Entry,
    Feature,
    GOAnnotation,
    MappingResult,
    SearchHit,
    Sequence,
    XRef,
)

GO_ASPECT_MAP: dict[str, str] = {
    # full names
    "biological process": "BP",
    "molecular function": "MF",
    "cellular component": "CC",
    # short forms (lower/upper)
    "bp": "BP",
    "bp ": "BP",
    "mf": "MF",
    "cc": "CC",
    "p": "BP",
    "f": "MF",
    "c": "CC",
    "P": "BP",
    "F": "MF",
    "C": "CC",
}


def _clean_go_aspect(value: str | None) -> str | None:
    if not value:
        return None
    stripped = value.strip()
    lowered = stripped.lower()
    mapped = GO_ASPECT_MAP.get(lowered)
    if mapped:
        return mapped
    mapped = GO_ASPECT_MAP.get(stripped)
    return mapped or None


def _properties_to_map(properties: Any) -> dict[str, str]:
    """Normalize UniProt cross-reference properties into a dictionary."""

    if isinstance(properties, dict):
        return {str(key): str(value) for key, value in properties.items() if value is not None}
    result: dict[str, str] = {}
    if isinstance(properties, list):
        for item in properties:
            if not isinstance(item, dict):
                continue
            key = item.get("key")
            value = item.get("value")
            if key is not None and value is not None:
                result[str(key)] = str(value)
    return result


def _extract_protein_name(entry: dict[str, Any]) -> str | None:
    protein = entry.get("proteinDescription") or {}
    recommended = protein.get("recommendedName") or {}
    full_name = recommended.get("fullName")
    if isinstance(full_name, dict):
        return full_name.get("value") or full_name.get("text")
    if isinstance(full_name, str):
        return full_name
    alternative = protein.get("alternativeNames")
    if isinstance(alternative, list):
        for alt in alternative:
            if isinstance(alt, dict):
                value = alt.get("fullName")
                if isinstance(value, dict):
                    text = value.get("value") or value.get("text")
                    if isinstance(text, str):
                        return text
                elif isinstance(value, str):
                    return value
    direct = recommended.get("value") if isinstance(recommended, dict) else None
    if isinstance(direct, str):
        return direct
    text = recommended.get("text") if isinstance(recommended, dict) else None
    if isinstance(text, str):
        return text
    return None


def _extract_gene_symbols(entry: dict[str, Any]) -> list[str]:
    genes: list[str] = []
    for gene in entry.get("genes", []) or []:
        primary = gene.get("geneName")
        if isinstance(primary, dict):
            name = primary.get("value") or primary.get("text")
            if name:
                genes.append(name)
        alternatives = (
            gene.get("synonyms")
            or gene.get("geneNameSynonyms")
            or gene.get("geneNameSynonym")
            or []
        )
        for alt in alternatives:
            if isinstance(alt, dict):
                value = alt.get("value") or alt.get("text")
                if value:
                    genes.append(value)
    return list(dict.fromkeys(genes))  # stable dedupe preserving order


def _extract_sequence(entry: dict[str, Any]) -> Sequence | None:
    raw_sequence = entry.get("sequence")
    if not isinstance(raw_sequence, dict):
        return None
    value = raw_sequence.get("value")
    length = raw_sequence.get("length")
    if value is None or length is None:
        return None
    return Sequence(
        length=int(length),
        value=value,
        mol_weight=(
            raw_sequence.get("mass")
            or raw_sequence.get("molWeight")
            or raw_sequence.get("molecularWeight")
        ),
        crc64=(
            raw_sequence.get("checksum")
            or raw_sequence.get("crc64")
            or raw_sequence.get("crc64Checksum")
        ),
    )


def _extract_features(entry: dict[str, Any]) -> list[Feature]:
    features: list[Feature] = []
    for raw_feature in entry.get("features") or []:
        if not isinstance(raw_feature, dict):
            continue
        location = raw_feature.get("location") or {}
        start_block = location.get("start") or {}
        end_block = location.get("end") or {}
        start = start_block.get("value")
        end = end_block.get("value")
        evidences = raw_feature.get("evidences") or []
        evidence_codes: list[str] = []
        for ev in evidences:
            if isinstance(ev, dict):
                code = ev.get("code") or ev.get("evidenceCode")
                if code:
                    evidence_codes.append(code)
        feature_type = str(raw_feature.get("type") or "").strip()
        if not feature_type:
            continue
        features.append(
            Feature(
                type=feature_type,
                start=_to_int_or_none(start),
                end=_to_int_or_none(end),
                description=raw_feature.get("description"),
                evidence=evidence_codes,
            )
        )
    return features


def _extract_go(entry: dict[str, Any]) -> list[GOAnnotation]:
    go_terms: list[GOAnnotation] = []
    raw_terms = entry.get("goTerms") or entry.get("uniProtKBGOTerms") or []
    for term in raw_terms or []:
        if not isinstance(term, dict):
            continue
        term_id = term.get("id") or term.get("termId")
        label = term.get("term") or term.get("label") or term.get("name")
        aspect = _clean_go_aspect(term.get("aspect") or term.get("category"))
        if not term_id or not label or not aspect:
            continue
        final_aspect = aspect if aspect in {"BP", "MF", "CC"} else "BP"
        go_terms.append(GOAnnotation(aspect=final_aspect, term=label, id=term_id))
    return go_terms


def _extract_xrefs(entry: dict[str, Any]) -> tuple[list[XRef], list[GOAnnotation]]:
    xrefs: list[XRef] = []
    go_terms: list[GOAnnotation] = []
    for xref in entry.get("uniProtKBCrossReferences") or []:
        if not isinstance(xref, dict):
            continue
        db = xref.get("database") or xref.get("db")
        identifier = xref.get("id") or xref.get("identifier")
        if not db or not identifier:
            continue
        prop_map = _properties_to_map(xref.get("properties"))
        url = prop_map.get("url")

        if str(db).upper() == "GO":
            term_name = prop_map.get("term") or prop_map.get("label") or prop_map.get("name")
            aspect = _clean_go_aspect(prop_map.get("aspect") or prop_map.get("category"))
            if aspect:
                go_terms.append(
                    GOAnnotation(
                        aspect=aspect if aspect in {"BP", "MF", "CC"} else "BP",
                        term=str(term_name or identifier),
                        id=str(identifier),
                    )
                )
            continue

        xrefs.append(XRef(db=str(db), id=str(identifier), url=url))
    return xrefs, go_terms


def _to_int_or_none(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def parse_entry(js: dict[str, Any]) -> Entry:
    """Convert a UniProt entry payload into the Entry model."""

    accession = js.get("primaryAccession") or js.get("accession")
    if not accession:
        raise ValueError("UniProt entry payload missing primary accession.")

    entry_type = js.get("entryType") or ""
    xrefs, go_terms = _extract_xrefs(js)

    entry = Entry(
        accession=str(accession),
        id=js.get("uniProtkbId") or js.get("id"),
        reviewed=entry_type.startswith("UniProtKB reviewed"),
        protein_name=_extract_protein_name(js),
        gene_symbols=_extract_gene_symbols(js),
        organism=(js.get("organism") or {}).get("scientificName")
        if isinstance(js.get("organism"), dict)
        else None,
        taxonomy_id=_to_int_or_none((js.get("organism") or {}).get("taxonId"))
        if isinstance(js.get("organism"), dict)
        else None,
        sequence=_extract_sequence(js),
        features=_extract_features(js),
        go=_extract_go(js) or go_terms,
        xrefs=xrefs,
        raw_payload=js,
    )
    return entry


def parse_sequence_from_entry(js: dict[str, Any]) -> Sequence | None:
    """Extract just the Sequence section from an entry payload."""

    return _extract_sequence(js)


def parse_search_hits(js: dict[str, Any]) -> list[SearchHit]:
    """Convert a UniProt search response into SearchHit models."""

    hits: list[SearchHit] = []
    for result in js.get("results") or []:
        if not isinstance(result, dict):
            continue
        accession = result.get("primaryAccession") or result.get("accession")
        if not accession:
            continue
        organism_block = result.get("organism", {})
        organism_name = (
            organism_block.get("scientificName") if isinstance(organism_block, dict) else None
        )
        entry_type = result.get("entryType") or ""
        hits.append(
            SearchHit(
                accession=str(accession),
                id=result.get("uniProtkbId") or result.get("id"),
                reviewed=str(entry_type).startswith("UniProtKB reviewed"),
                protein_name=_extract_protein_name(result),
                organism=organism_name,
            )
        )
    return hits


def parse_mapping_result(
    js: dict[str, Any],
    *,
    from_db: str,
    to_db: str,
) -> MappingResult:
    """Convert an ID mapping response into MappingResult."""

    mappings: dict[str, list[str]] = {}

    def register_result(source: str | None, targets: Iterable[Any]) -> None:
        if not source:
            return
        values: list[str] = []
        for target in targets:
            if isinstance(target, dict):
                candidate = target.get("id") or target.get("identifier") or target.get("value")
                if candidate:
                    values.append(str(candidate))
            elif target is not None:
                values.append(str(target))
        if source not in mappings:
            mappings[source] = []
        mappings[source].extend(values)

    for item in js.get("results") or []:
        if not isinstance(item, dict):
            continue
        source = item.get("from") or item.get("fromId")
        to_value = item.get("to") or item.get("toId") or item.get("mappedTo")
        if isinstance(to_value, list):
            register_result(source, to_value)
        elif to_value is not None:
            register_result(source, [to_value])
        else:
            register_result(source, [])

    # Some responses return an explicit mapping dictionary
    for source, value in (js.get("mappedResults") or {}).items():
        if isinstance(value, list):
            register_result(source, value)
        else:
            register_result(source, [value])

    # Ensure failed IDs are tracked with empty lists
    for failed in js.get("failedIds") or []:
        if failed not in mappings:
            mappings[failed] = []

    # Normalise ordering and remove duplicates per ID
    for key, values in mappings.items():
        deduped = list(dict.fromkeys(values))
        mappings[key] = deduped

    return MappingResult(from_db=from_db, to_db=to_db, results=mappings)
