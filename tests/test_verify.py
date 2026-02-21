"""Tests for CURIE verification and LinkML schema generation."""

from textwrap import dedent

import pytest

from microbial_trait_mappings.verify import build_validation_schema


@pytest.fixture
def data_dir_with_mappings(tmp_path):
    """Create a temp data dir with a populated positive mapping TSV."""
    chem_dir = tmp_path / "chemicals"
    chem_dir.mkdir()
    (chem_dir / "chemical_mappings.tsv").write_text(
        dedent("""\
            subject_label\tobject_id\tobject_label\tobject_source\tpredicate_id
            glucose\tCHEBI:17234\tglucose\tCHEBI\tskos:exactMatch
            sucrose\tCHEBI:17992\tsucrose\tCHEBI\tskos:exactMatch
        """),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def empty_data_dir(tmp_path):
    """Create a temp data dir with header-only TSV."""
    chem_dir = tmp_path / "chemicals"
    chem_dir.mkdir()
    (chem_dir / "chemical_mappings.tsv").write_text(
        "subject_label\tobject_id\tobject_label\tobject_source\tpredicate_id\n",
        encoding="utf-8",
    )
    return tmp_path


class TestBuildValidationSchema:
    """LinkML schema generation from mapping TSVs."""

    def test_generates_schema_structure(self, data_dir_with_mappings):
        schema = build_validation_schema(data_dir_with_mappings)
        assert "id" in schema
        assert "enums" in schema
        assert "prefixes" in schema

    def test_creates_enum_per_source(self, data_dir_with_mappings):
        schema = build_validation_schema(data_dir_with_mappings)
        assert "CHEBIMappingEnum" in schema["enums"]

    def test_permissible_values_have_meaning(self, data_dir_with_mappings):
        schema = build_validation_schema(data_dir_with_mappings)
        pvs = schema["enums"]["CHEBIMappingEnum"]["permissible_values"]
        meanings = {v["meaning"] for v in pvs.values()}
        assert "CHEBI:17234" in meanings
        assert "CHEBI:17992" in meanings

    def test_permissible_values_have_title(self, data_dir_with_mappings):
        schema = build_validation_schema(data_dir_with_mappings)
        pvs = schema["enums"]["CHEBIMappingEnum"]["permissible_values"]
        titles = {v["title"] for v in pvs.values()}
        assert "glucose" in titles

    def test_empty_data_produces_empty_enums(self, empty_data_dir):
        schema = build_validation_schema(empty_data_dir)
        assert schema["enums"] == {}

    def test_no_tsv_files(self, tmp_path):
        schema = build_validation_schema(tmp_path)
        assert schema["enums"] == {}

    def test_multiple_sources(self, tmp_path):
        """Multiple source ontologies produce separate enums."""
        chem_dir = tmp_path / "chemicals"
        chem_dir.mkdir()
        (chem_dir / "chemical_mappings.tsv").write_text(
            dedent("""\
                subject_label\tobject_id\tobject_label\tobject_source\tpredicate_id
                glucose\tCHEBI:17234\tglucose\tCHEBI\tskos:exactMatch
            """),
            encoding="utf-8",
        )
        path_dir = tmp_path / "pathways"
        path_dir.mkdir()
        (path_dir / "pathway_mappings.tsv").write_text(
            dedent("""\
                subject_label\tobject_id\tobject_label\tobject_source\tpredicate_id
                glycolysis\tGO:0006096\tglycolytic process\tGO\tskos:closeMatch
            """),
            encoding="utf-8",
        )
        schema = build_validation_schema(tmp_path)
        assert "CHEBIMappingEnum" in schema["enums"]
        assert "GOMappingEnum" in schema["enums"]
