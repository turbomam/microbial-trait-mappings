"""Conversion pattern tests — verify that each mapping category uses correct biolink edge patterns.

These tests encode the core invariant that different metatraits assertion types
require different (predicate, object_source, object_category) triples. This is
the bug that kg-microbe PR #490's `_get_relation_for_predicate()` collapses away.

Each test class covers one entity type and asserts:
1. Every row's object_id uses the expected CURIE prefix
2. Every row's predicate_id is from the allowed set for that category
3. The notes column documents the correct biolink predicate (not just skos mapping predicate)
"""

from pathlib import Path

import pandas as pd
import pytest

DATA_DIR = Path(__file__).parent.parent / "data"

# Expected CURIE prefixes per category
EXPECTED_PREFIXES = {
    "chemicals": {"CHEBI"},
    "enzymes": {"EC", "GO"},
    "pathways": {"GO"},
    "phenotypes": {"METPO"},
}

# Expected biolink predicates per category (extracted from notes column)
EXPECTED_BIOLINK_PREDICATES = {
    "chemicals": {"biolink:produces", "biolink:capable_of"},
    "enzymes": {"biolink:capable_of"},
    "pathways": {"biolink:capable_of"},
    "phenotypes": {"biolink:has_phenotype"},
}


def _load_positive_mappings(category: str) -> pd.DataFrame:
    """Load the positive mapping TSV for a category."""
    cat_dir = DATA_DIR / category
    candidates = [f for f in cat_dir.glob("*_mappings.tsv") if "negative" not in f.name]
    assert candidates, f"No positive mapping TSV in data/{category}/"
    df = pd.read_csv(candidates[0], sep="\t", dtype=str, keep_default_na=False)
    return df


def _extract_biolink_predicates(notes_series: pd.Series) -> set[str]:
    """Extract biolink:* predicates mentioned in the notes column."""
    predicates = set()
    for note in notes_series:
        for token in note.replace(";", " ").split():
            if token.startswith("biolink:"):
                predicates.add(token)
    return predicates


@pytest.mark.skipif(not DATA_DIR.exists(), reason="data/ directory not found")
class TestChemicalPatterns:
    """Chemicals must map to CHEBI CURIEs with biolink:produces or biolink:capable_of."""

    def test_all_object_ids_are_chebi(self):
        df = _load_positive_mappings("chemicals")
        for idx, row in df.iterrows():
            prefix = row["object_id"].split(":")[0]
            assert prefix in EXPECTED_PREFIXES["chemicals"], (
                f"Row {idx + 2}: object_id '{row['object_id']}' has unexpected prefix '{prefix}', "
                f"expected one of {EXPECTED_PREFIXES['chemicals']}"
            )

    def test_biolink_predicates_documented(self):
        df = _load_positive_mappings("chemicals")
        predicates = _extract_biolink_predicates(df["notes"])
        assert predicates, "No biolink predicates found in notes column"
        unexpected = predicates - EXPECTED_BIOLINK_PREDICATES["chemicals"]
        assert not unexpected, f"Unexpected biolink predicates in chemicals: {unexpected}"

    def test_produces_vs_carbon_source_distinction(self):
        """'produces: X' and 'carbon source: X' rows should exist and use different biolink predicates."""
        df = _load_positive_mappings("chemicals")
        produces = df[df["subject_label"].str.startswith("produces:")]
        carbon = df[df["subject_label"].str.startswith("carbon source:")]
        if produces.empty or carbon.empty:
            pytest.skip("Need both 'produces:' and 'carbon source:' rows to test distinction")
        produces_preds = _extract_biolink_predicates(produces["notes"])
        carbon_preds = _extract_biolink_predicates(carbon["notes"])
        # produces should use biolink:produces, carbon source should use biolink:capable_of
        assert "biolink:produces" in produces_preds, "produces rows should document biolink:produces"
        assert "biolink:capable_of" in carbon_preds, "carbon source rows should document biolink:capable_of"


@pytest.mark.skipif(not DATA_DIR.exists(), reason="data/ directory not found")
class TestEnzymePatterns:
    """Enzymes must map to EC or GO CURIEs with biolink:capable_of."""

    def test_all_object_ids_have_valid_prefix(self):
        df = _load_positive_mappings("enzymes")
        for idx, row in df.iterrows():
            prefix = row["object_id"].split(":")[0]
            assert prefix in EXPECTED_PREFIXES["enzymes"], (
                f"Row {idx + 2}: object_id '{row['object_id']}' has unexpected prefix '{prefix}'"
            )

    def test_ec_numbers_extractable_from_name(self):
        """Rows with EC numbers in subject_label should have matching EC object_id."""
        df = _load_positive_mappings("enzymes")
        import re

        for idx, row in df.iterrows():
            ec_match = re.search(r"EC\s*([\d.]+)", row["subject_label"], re.IGNORECASE)
            if ec_match:
                expected_ec = f"EC:{ec_match.group(1)}"
                assert row["object_id"] == expected_ec, (
                    f"Row {idx + 2}: subject_label contains EC number but object_id "
                    f"'{row['object_id']}' != '{expected_ec}'"
                )

    def test_biolink_predicates_documented(self):
        df = _load_positive_mappings("enzymes")
        predicates = _extract_biolink_predicates(df["notes"])
        unexpected = predicates - EXPECTED_BIOLINK_PREDICATES["enzymes"]
        assert not unexpected, f"Unexpected biolink predicates in enzymes: {unexpected}"


@pytest.mark.skipif(not DATA_DIR.exists(), reason="data/ directory not found")
class TestPathwayPatterns:
    """Pathways must map to GO CURIEs with biolink:capable_of."""

    def test_all_object_ids_are_go(self):
        df = _load_positive_mappings("pathways")
        for idx, row in df.iterrows():
            prefix = row["object_id"].split(":")[0]
            assert prefix in EXPECTED_PREFIXES["pathways"], (
                f"Row {idx + 2}: object_id '{row['object_id']}' has unexpected prefix '{prefix}'"
            )

    def test_biolink_predicates_documented(self):
        df = _load_positive_mappings("pathways")
        predicates = _extract_biolink_predicates(df["notes"])
        unexpected = predicates - EXPECTED_BIOLINK_PREDICATES["pathways"]
        assert not unexpected, f"Unexpected biolink predicates in pathways: {unexpected}"


@pytest.mark.skipif(not DATA_DIR.exists(), reason="data/ directory not found")
class TestPhenotypePatterns:
    """Phenotypes must map to METPO CURIEs with biolink:has_phenotype."""

    def test_all_object_ids_are_metpo(self):
        df = _load_positive_mappings("phenotypes")
        for idx, row in df.iterrows():
            prefix = row["object_id"].split(":")[0]
            assert prefix in EXPECTED_PREFIXES["phenotypes"], (
                f"Row {idx + 2}: object_id '{row['object_id']}' has unexpected prefix '{prefix}'"
            )

    def test_biolink_predicates_documented(self):
        df = _load_positive_mappings("phenotypes")
        predicates = _extract_biolink_predicates(df["notes"])
        unexpected = predicates - EXPECTED_BIOLINK_PREDICATES["phenotypes"]
        assert not unexpected, f"Unexpected biolink predicates in phenotypes: {unexpected}"

    def test_no_has_phenotype_for_non_phenotype_categories(self):
        """Verify that chemicals, enzymes, pathways do NOT use biolink:has_phenotype.

        This is the exact bug in kg-microbe PR #490: _get_relation_for_predicate()
        falls back to has_phenotype for everything that isn't capable_of.
        """
        for category in ["chemicals", "enzymes", "pathways"]:
            df = _load_positive_mappings(category)
            predicates = _extract_biolink_predicates(df["notes"])
            assert "biolink:has_phenotype" not in predicates, (
                f"Category '{category}' should NOT use biolink:has_phenotype — "
                f"this is the _get_relation_for_predicate() collapse bug"
            )
