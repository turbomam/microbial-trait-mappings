"""CURIE verification via OAK and LinkML schema generation.

Reads positive mapping TSVs and:
1. Generates a LinkML schema where each CURIE is a permissible_value with a meaning field
2. Verifies CURIEs exist in their source ontology via OAK
3. Confirms canonical labels match expected labels
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml


@dataclass
class ValidationResult:
    """Result of verifying a single CURIE."""

    curie: str
    expected_label: str
    actual_label: str | None
    status: str  # "valid", "label_mismatch", "not_found", "error"
    severity: str  # "ok", "warning", "error"
    source_file: str = ""
    message: str = ""


@dataclass
class VerificationReport:
    """Aggregated CURIE verification results."""

    results: list[ValidationResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(r.severity == "error" for r in self.results)

    @property
    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self.results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts


def _read_positive_mappings(data_dir: Path) -> pd.DataFrame:
    """Read all positive mapping TSVs from a data directory."""
    frames = []
    for tsv_path in sorted(data_dir.rglob("*.tsv")):
        if "negative" in tsv_path.stem:
            continue
        try:
            df = pd.read_csv(tsv_path, sep="\t", dtype=str, keep_default_na=False)
        except Exception:
            continue
        if df.empty or "object_id" not in df.columns:
            continue
        df["_source_file"] = str(tsv_path)
        frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_validation_schema(data_dir: Path) -> dict:
    """Generate a LinkML-style validation schema from positive mapping TSVs.

    Each unique CURIE becomes a permissible_value with a ``meaning`` field
    that tools like linkml-term-validator can verify against source ontologies.

    Args:
        data_dir: Path to the data/ directory.

    Returns:
        A dict representing the LinkML schema YAML.
    """
    df = _read_positive_mappings(data_dir)

    enums: dict[str, dict] = {}

    if df.empty:
        return _wrap_schema(enums)

    # Group by source ontology to create separate enums
    for source, group in df.groupby("object_source"):
        source_str = str(source).strip()
        if not source_str:
            continue

        enum_name = f"{source_str}MappingEnum"
        pvs: dict[str, dict] = {}

        for _, row in group.iterrows():
            curie = str(row.get("object_id", "")).strip()
            label = str(row.get("object_label", "")).strip()
            subj = str(row.get("subject_label", "")).strip()

            if not curie:
                continue

            # Use normalized subject_label as the key
            key = subj.lower().replace(" ", "_") if subj else curie.replace(":", "_").lower()
            # Deduplicate keys
            if key in pvs:
                key = f"{key}_{curie.replace(':', '_').lower()}"

            pvs[key] = {
                "title": subj or label,
                "meaning": curie,
            }

        if pvs:
            enums[enum_name] = {"permissible_values": pvs}

    return _wrap_schema(enums)


def _wrap_schema(enums: dict) -> dict:
    """Wrap enums in a minimal LinkML schema structure."""
    return {
        "id": "https://w3id.org/turbomam/microbial-trait-mappings",
        "name": "microbial_trait_mappings_validation",
        "title": "Microbial Trait Mappings Validation Schema",
        "description": "Auto-generated schema for CURIE verification via linkml-term-validator.",
        "prefixes": {
            "linkml": "https://w3id.org/linkml/",
            "CHEBI": "http://purl.obolibrary.org/obo/CHEBI_",
            "GO": "http://purl.obolibrary.org/obo/GO_",
            "OMP": "http://purl.obolibrary.org/obo/OMP_",
            "MICRO": "http://purl.obolibrary.org/obo/MICRO_",
            "FOODON": "http://purl.obolibrary.org/obo/FOODON_",
            "ENVO": "http://purl.obolibrary.org/obo/ENVO_",
            "PATO": "http://purl.obolibrary.org/obo/PATO_",
            "EC": "https://identifiers.org/ec-code/",
        },
        "default_range": "string",
        "enums": enums if enums else {},
    }


def write_validation_schema(schema: dict, output_path: Path) -> None:
    """Write the validation schema to a YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def verify_curies_via_oak(data_dir: Path, oak_config_path: Path) -> VerificationReport:
    """Verify all CURIEs in positive mappings against source ontologies via OAK.

    Args:
        data_dir: Path to data/ directory.
        oak_config_path: Path to OAK adapter config YAML.

    Returns:
        VerificationReport with results for each CURIE.
    """
    report = VerificationReport()

    # Load OAK config
    with oak_config_path.open(encoding="utf-8") as f:
        oak_config = yaml.safe_load(f) or {}

    adapters = oak_config.get("ontology_adapters", {})

    df = _read_positive_mappings(data_dir)
    if df.empty:
        return report

    # Group by source and verify
    for source, group in df.groupby("object_source"):
        source_str = str(source).strip()
        adapter_spec = adapters.get(source_str)

        if not adapter_spec:
            for _, row in group.iterrows():
                report.results.append(
                    ValidationResult(
                        curie=str(row.get("object_id", "")),
                        expected_label=str(row.get("object_label", "")),
                        actual_label=None,
                        status="no_adapter",
                        severity="warning",
                        source_file=str(row.get("_source_file", "")),
                        message=f"No OAK adapter configured for source: {source_str}",
                    )
                )
            continue

        try:
            from oaklib import get_adapter

            adapter = get_adapter(adapter_spec)
        except Exception as exc:
            for _, row in group.iterrows():
                report.results.append(
                    ValidationResult(
                        curie=str(row.get("object_id", "")),
                        expected_label=str(row.get("object_label", "")),
                        actual_label=None,
                        status="error",
                        severity="error",
                        source_file=str(row.get("_source_file", "")),
                        message=f"Failed to load OAK adapter '{adapter_spec}': {exc}",
                    )
                )
            continue

        # Collect all CURIEs for batch lookup
        curies = set()
        for _, row in group.iterrows():
            curie = str(row.get("object_id", "")).strip()
            if curie:
                curies.add(curie)

        # Batch label lookup
        labels: dict[str, str | None] = {}
        for curie, label in adapter.labels(curies):
            labels[curie] = label
        for curie in curies:
            if curie not in labels:
                labels[curie] = None

        # Verify each mapping
        for _, row in group.iterrows():
            curie = str(row.get("object_id", "")).strip()
            expected = str(row.get("object_label", "")).strip()
            source_file = str(row.get("_source_file", ""))

            if not curie:
                continue

            actual = labels.get(curie)

            if actual is None:
                report.results.append(
                    ValidationResult(
                        curie=curie,
                        expected_label=expected,
                        actual_label=None,
                        status="not_found",
                        severity="error",
                        source_file=source_file,
                        message=f"CURIE {curie} not found in {source_str}",
                    )
                )
            elif actual.strip().lower() == expected.strip().lower():
                report.results.append(
                    ValidationResult(
                        curie=curie,
                        expected_label=expected,
                        actual_label=actual,
                        status="valid",
                        severity="ok",
                        source_file=source_file,
                    )
                )
            else:
                report.results.append(
                    ValidationResult(
                        curie=curie,
                        expected_label=expected,
                        actual_label=actual,
                        status="label_mismatch",
                        severity="error",
                        source_file=source_file,
                        message=f"Expected '{expected}', got '{actual}'",
                    )
                )

    return report
