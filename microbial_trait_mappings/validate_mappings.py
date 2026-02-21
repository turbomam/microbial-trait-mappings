"""Validate mapping TSV column schemas.

Checks that all TSV files in the data directory have the required columns
and that required fields are non-empty.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# Required columns for positive mapping TSVs
POSITIVE_REQUIRED_COLUMNS = [
    "subject_label",
    "object_id",
    "object_label",
    "object_source",
    "predicate_id",
]

POSITIVE_ALL_COLUMNS = [
    "subject_label",
    "subject_label_normalized",
    "object_id",
    "object_label",
    "object_source",
    "predicate_id",
    "confidence",
    "mapping_justification",
    "curator",
    "source_dataset",
    "notes",
    "verified_date",
]

# Required columns for negative mapping TSVs
NEGATIVE_REQUIRED_COLUMNS = [
    "subject_label",
    "rejected_object_id",
    "rejected_object_label",
    "rejection_reason",
    "reported_date",
]

NEGATIVE_ALL_COLUMNS = [
    "subject_label",
    "rejected_object_id",
    "rejected_object_label",
    "correct_object_id",
    "correct_object_label",
    "rejection_reason",
    "provenance",
    "reported_date",
    "reporter",
]

VALID_PREDICATES = {
    "skos:exactMatch",
    "skos:closeMatch",
    "skos:broadMatch",
    "skos:narrowMatch",
    "skos:relatedMatch",
}


@dataclass
class ValidationError:
    """A single validation error."""

    file: str
    row: int | None
    column: str | None
    message: str
    severity: str = "error"


@dataclass
class ValidationReport:
    """Aggregated validation results."""

    errors: list[ValidationError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(e.severity == "error" for e in self.errors)

    def add(self, file: str, row: int | None, column: str | None, message: str, severity: str = "error") -> None:
        self.errors.append(ValidationError(file=file, row=row, column=column, message=message, severity=severity))


def _is_negative_file(path: Path) -> bool:
    return "negative" in path.stem


def validate_tsv(path: Path, report: ValidationReport) -> None:
    """Validate a single TSV file against its expected schema."""
    fname = str(path)

    try:
        df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    except Exception as exc:
        report.add(fname, None, None, f"Failed to read TSV: {exc}")
        return

    if df.empty:
        # Empty data files (header-only) are OK
        return

    is_negative = _is_negative_file(path)
    required = NEGATIVE_REQUIRED_COLUMNS if is_negative else POSITIVE_REQUIRED_COLUMNS
    all_cols = NEGATIVE_ALL_COLUMNS if is_negative else POSITIVE_ALL_COLUMNS

    # Check required columns exist
    for col in required:
        if col not in df.columns:
            report.add(fname, None, col, f"Missing required column: {col}")

    # Warn on unexpected columns
    for col in df.columns:
        if col not in all_cols:
            report.add(fname, None, col, f"Unexpected column: {col}", severity="warning")

    # Check required fields are non-empty
    for col in required:
        if col not in df.columns:
            continue
        empty_rows = df[df[col].str.strip() == ""]
        for idx in empty_rows.index:
            report.add(fname, int(idx) + 2, col, f"Empty required field: {col}")  # +2 for 1-indexed + header

    # Validate predicate_id values for positive mappings
    if not is_negative and "predicate_id" in df.columns:
        for idx, row in df.iterrows():
            pred = row["predicate_id"].strip()
            if pred and pred not in VALID_PREDICATES:
                report.add(fname, int(idx) + 2, "predicate_id", f"Invalid predicate: {pred}")

    # Validate CURIE format for object_id / rejected_object_id
    curie_col = "rejected_object_id" if is_negative else "object_id"
    if curie_col in df.columns:
        for idx, row in df.iterrows():
            curie = row[curie_col].strip()
            if curie and ":" not in curie:
                report.add(fname, int(idx) + 2, curie_col, f"Invalid CURIE format (missing ':'): {curie}")


def validate_directory(data_dir: Path) -> ValidationReport:
    """Validate all TSV files in a data directory."""
    report = ValidationReport()

    tsv_files = sorted(data_dir.rglob("*.tsv"))
    if not tsv_files:
        report.add(str(data_dir), None, None, "No TSV files found in data directory")
        return report

    for path in tsv_files:
        validate_tsv(path, report)

    return report
