"""Data integrity tests — validates all data/*.tsv files on every PR.

These tests operate on the actual data files in the repository, not test fixtures.
They ensure that committed data always meets the schema requirements.
"""

from pathlib import Path

import pytest

from microbial_trait_mappings.validate_mappings import validate_directory

# Path to the actual data directory (relative to project root)
DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.mark.skipif(not DATA_DIR.exists(), reason="data/ directory not found")
class TestDataIntegrity:
    """Validate all committed TSV files."""

    def test_data_directory_exists(self):
        assert DATA_DIR.is_dir()

    def test_all_tsvs_valid_schema(self):
        """Every TSV in data/ must pass column schema validation."""
        report = validate_directory(DATA_DIR)
        errors = [e for e in report.errors if e.severity == "error"]
        if errors:
            msg = "\n".join(f"  {e.file}:{e.row} [{e.column}] {e.message}" for e in errors)
            pytest.fail(f"TSV validation errors:\n{msg}")

    def test_all_categories_have_positive_mapping(self):
        """Each category directory should have a positive mapping TSV."""
        categories = ["chemicals", "enzymes", "pathways", "phenotypes"]
        for cat in categories:
            cat_dir = DATA_DIR / cat
            if not cat_dir.exists():
                pytest.fail(f"Missing category directory: data/{cat}/")
            # Allow either singular or plural in filename
            candidates = list(cat_dir.glob("*_mappings.tsv"))
            candidates = [c for c in candidates if "negative" not in c.name]
            assert candidates, f"No positive mapping TSV in data/{cat}/"

    def test_all_categories_have_negative_mapping(self):
        """Each category directory should have a negative mapping TSV."""
        categories = ["chemicals", "enzymes", "pathways", "phenotypes"]
        for cat in categories:
            cat_dir = DATA_DIR / cat
            if not cat_dir.exists():
                continue
            negatives = list(cat_dir.glob("*negative*mappings.tsv"))
            assert negatives, f"No negative mapping TSV in data/{cat}/"

    def test_no_duplicate_curies_in_positive_mappings(self):
        """Each positive mapping TSV should not have duplicate (subject_label, object_id) pairs."""
        import pandas as pd

        for tsv_path in sorted(DATA_DIR.rglob("*.tsv")):
            if "negative" in tsv_path.stem:
                continue
            try:
                df = pd.read_csv(tsv_path, sep="\t", dtype=str, keep_default_na=False)
            except Exception:
                continue
            if df.empty or "subject_label" not in df.columns or "object_id" not in df.columns:
                continue
            dupes = df[df.duplicated(subset=["subject_label", "object_id"], keep=False)]
            if not dupes.empty:
                pytest.fail(f"Duplicate (subject_label, object_id) in {tsv_path.name}: {dupes.to_dict('records')}")
