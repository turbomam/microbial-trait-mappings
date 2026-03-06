"""Round-trip tests — simulate the metatraits→KGX edge resolution pipeline.

These tests implement a minimal version of kg-microbe's trait→edge conversion
to prove that each mapping row produces a semantically correct KGX edge triple.

The round trip is:
  metatraits subject_label → lookup in mapping TSV → (biolink_predicate, object_id, object_source)

This catches the core bug: if the lookup falls back to a single predicate
(e.g., always has_phenotype), these tests fail for non-phenotype categories.
"""

from pathlib import Path

import pandas as pd
import pytest

DATA_DIR = Path(__file__).parent.parent / "data"

# The correct biolink predicate for each subject_label pattern.
# This is the truth table that kg-microbe's _get_relation_for_predicate() should implement.
EXPECTED_EDGES: dict[str, dict] = {
    # chemicals — "produces:" prefix → biolink:produces
    "produces: ethanol": {
        "biolink_predicate": "biolink:produces",
        "object_id": "CHEBI:16236",
        "object_category": "biolink:ChemicalEntity",
    },
    "produces: hydrogen sulfide": {
        "biolink_predicate": "biolink:produces",
        "object_id": "CHEBI:16136",
        "object_category": "biolink:ChemicalEntity",
    },
    "produces: indole": {
        "biolink_predicate": "biolink:produces",
        "object_id": "CHEBI:16881",
        "object_category": "biolink:ChemicalEntity",
    },
    # chemicals — "carbon source:" prefix → biolink:capable_of (carbon utilization process)
    "carbon source: acetate": {
        "biolink_predicate": "biolink:capable_of",
        "object_id": "CHEBI:30089",
        "object_category": "biolink:ChemicalEntity",
    },
    # enzymes — EC extractable → biolink:capable_of, object is enzyme activity
    "enzyme activity: catalase (EC1.11.1.6)": {
        "biolink_predicate": "biolink:capable_of",
        "object_id": "EC:1.11.1.6",
        "object_category": "biolink:MolecularActivity",
    },
    "enzyme activity: urease (EC3.5.1.5)": {
        "biolink_predicate": "biolink:capable_of",
        "object_id": "EC:3.5.1.5",
        "object_category": "biolink:MolecularActivity",
    },
    # enzymes — no EC in name → biolink:capable_of, broader match
    "enzyme activity: oxidase": {
        "biolink_predicate": "biolink:capable_of",
        "object_id": "GO:0016491",
        "object_category": "biolink:MolecularActivity",
    },
    # pathways → biolink:capable_of, object is biological process
    "fermentation": {
        "biolink_predicate": "biolink:capable_of",
        "object_id": "GO:0006113",
        "object_category": "biolink:BiologicalProcess",
    },
    "nitrogen fixation": {
        "biolink_predicate": "biolink:capable_of",
        "object_id": "GO:0009399",
        "object_category": "biolink:BiologicalProcess",
    },
    # phenotypes → biolink:has_phenotype
    "gram positive": {
        "biolink_predicate": "biolink:has_phenotype",
        "object_id": "METPO:1000606",
        "object_category": "biolink:PhenotypicFeature",
    },
    "obligate aerobic": {
        "biolink_predicate": "biolink:has_phenotype",
        "object_id": "METPO:1000616",
        "object_category": "biolink:PhenotypicFeature",
    },
    "thermophilic": {
        "biolink_predicate": "biolink:has_phenotype",
        "object_id": "METPO:1000656",
        "object_category": "biolink:PhenotypicFeature",
    },
}


def _resolve_biolink_predicate(subject_label: str, notes: str) -> str:
    """Derive the correct biolink predicate from mapping row metadata.

    This is what kg-microbe's transform SHOULD do instead of collapsing
    everything to has_phenotype.
    """
    for token in notes.replace(";", " ").split():
        if token.startswith("biolink:"):
            return token
    # Fallback heuristics based on subject_label pattern
    if subject_label.startswith("produces:"):
        return "biolink:produces"
    if subject_label.startswith("carbon source:") or subject_label.startswith("enzyme activity:"):
        return "biolink:capable_of"
    return "biolink:has_phenotype"


def _resolve_object_category(object_source: str, biolink_predicate: str, category: str = "") -> str:
    """Derive KGX object category from source ontology, predicate, and mapping category."""
    if object_source == "CHEBI":
        return "biolink:ChemicalEntity"
    if object_source == "EC":
        return "biolink:MolecularActivity"
    if object_source == "METPO":
        return "biolink:PhenotypicFeature"
    if object_source == "GO":
        # GO terms in the enzymes category are molecular functions, not biological processes
        if category == "enzymes":
            return "biolink:MolecularActivity"
        return "biolink:BiologicalProcess"
    return "biolink:NamedThing"


def _load_all_mappings() -> pd.DataFrame:
    """Load and concatenate all positive mapping TSVs."""
    frames = []
    for tsv in sorted(DATA_DIR.rglob("*.tsv")):
        if "negative" in tsv.name:
            continue
        df = pd.read_csv(tsv, sep="\t", dtype=str, keep_default_na=False)
        if not df.empty:
            df["_category"] = tsv.parent.name
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@pytest.mark.skipif(not DATA_DIR.exists(), reason="data/ directory not found")
class TestRoundTrip:
    """For each expected edge, look it up in the mapping TSVs and verify the triple."""

    @pytest.fixture(scope="class")
    def all_mappings(self) -> pd.DataFrame:
        return _load_all_mappings()

    @pytest.mark.parametrize("subject_label,expected", list(EXPECTED_EDGES.items()))
    def test_edge_resolution(self, all_mappings, subject_label, expected):
        """Given a metatraits subject_label, resolve it to a KGX edge and check correctness."""
        matches = all_mappings[all_mappings["subject_label"] == subject_label]
        assert not matches.empty, f"No mapping found for subject_label '{subject_label}'"
        assert len(matches) == 1, f"Multiple mappings for '{subject_label}': expected exactly 1"

        row = matches.iloc[0]

        # Check object_id
        assert row["object_id"] == expected["object_id"], (
            f"object_id mismatch: got '{row['object_id']}', expected '{expected['object_id']}'"
        )

        # Resolve biolink predicate from notes
        biolink_pred = _resolve_biolink_predicate(row["subject_label"], row["notes"])
        assert biolink_pred == expected["biolink_predicate"], (
            f"biolink predicate mismatch for '{subject_label}': "
            f"got '{biolink_pred}', expected '{expected['biolink_predicate']}'"
        )

        # Resolve object category
        object_cat = _resolve_object_category(row["object_source"], biolink_pred, row.get("_category", ""))
        assert object_cat == expected["object_category"], (
            f"object category mismatch for '{subject_label}': "
            f"got '{object_cat}', expected '{expected['object_category']}'"
        )


@pytest.mark.skipif(not DATA_DIR.exists(), reason="data/ directory not found")
class TestCollapseDetection:
    """Tests that specifically detect the _get_relation_for_predicate() collapse bug."""

    @pytest.fixture(scope="class")
    def all_mappings(self) -> pd.DataFrame:
        return _load_all_mappings()

    def test_not_all_predicates_are_has_phenotype(self, all_mappings):
        """If every row resolves to has_phenotype, the collapse bug is present."""
        predicates = set()
        for _, row in all_mappings.iterrows():
            pred = _resolve_biolink_predicate(row["subject_label"], row["notes"])
            predicates.add(pred)
        assert len(predicates) > 1, (
            "All rows resolve to a single biolink predicate — "
            "this indicates the _get_relation_for_predicate() collapse bug"
        )
        assert "biolink:produces" in predicates, "Missing biolink:produces — chemical 'produces:' rows broken"
        assert "biolink:capable_of" in predicates, "Missing biolink:capable_of — enzyme/pathway rows broken"
        assert "biolink:has_phenotype" in predicates, "Missing biolink:has_phenotype — phenotype rows broken"

    def test_produces_ethanol_is_not_has_phenotype(self, all_mappings):
        """The canonical example of the collapse bug: 'produces: ethanol' must NOT be has_phenotype."""
        matches = all_mappings[all_mappings["subject_label"] == "produces: ethanol"]
        if matches.empty:
            pytest.skip("'produces: ethanol' not in mappings yet")
        row = matches.iloc[0]
        pred = _resolve_biolink_predicate(row["subject_label"], row["notes"])
        assert pred != "biolink:has_phenotype", (
            "'produces: ethanol' resolved to biolink:has_phenotype — "
            "this is the exact bug in kg-microbe PR #490"
        )
