"""Tests for TSV column schema validation."""

from pathlib import Path
from textwrap import dedent

import pytest

from microbial_trait_mappings.validate_mappings import ValidationReport, validate_directory, validate_tsv


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temp data directory with subdirs."""
    (tmp_path / "chemicals").mkdir()
    return tmp_path


def _write_tsv(path: Path, content: str) -> Path:
    """Write a TSV file from dedented content."""
    path.write_text(dedent(content).lstrip(), encoding="utf-8")
    return path


class TestPositiveMappingValidation:
    """Positive mapping TSV validation."""

    def test_valid_file(self, tmp_data_dir):
        tsv = _write_tsv(
            tmp_data_dir / "chemicals" / "chemical_mappings.tsv",
            """\
            subject_label\tsubject_label_normalized\tobject_id\tobject_label\tobject_source\tpredicate_id\tconfidence\tmapping_justification\tcurator\tsource_dataset\tnotes\tverified_date
            glucose\tglucose\tCHEBI:17234\tglucose\tCHEBI\tskos:exactMatch\t1.0\t\t\t\t\t
            """,
        )
        report = ValidationReport()
        validate_tsv(tsv, report)
        assert report.ok

    def test_missing_required_column(self, tmp_data_dir):
        tsv = _write_tsv(
            tmp_data_dir / "chemicals" / "chemical_mappings.tsv",
            """\
            subject_label\tobject_label\tobject_source\tpredicate_id
            glucose\tglucose\tCHEBI\tskos:exactMatch
            """,
        )
        report = ValidationReport()
        validate_tsv(tsv, report)
        assert not report.ok
        missing = [e for e in report.errors if "Missing required column" in e.message]
        assert any("object_id" in e.message for e in missing)

    def test_empty_required_field(self, tmp_data_dir):
        tsv = _write_tsv(
            tmp_data_dir / "chemicals" / "chemical_mappings.tsv",
            """\
            subject_label\tobject_id\tobject_label\tobject_source\tpredicate_id
            \tCHEBI:17234\tglucose\tCHEBI\tskos:exactMatch
            """,
        )
        report = ValidationReport()
        validate_tsv(tsv, report)
        assert not report.ok

    def test_invalid_predicate(self, tmp_data_dir):
        tsv = _write_tsv(
            tmp_data_dir / "chemicals" / "chemical_mappings.tsv",
            """\
            subject_label\tobject_id\tobject_label\tobject_source\tpredicate_id
            glucose\tCHEBI:17234\tglucose\tCHEBI\tskos:fooMatch
            """,
        )
        report = ValidationReport()
        validate_tsv(tsv, report)
        errors = [e for e in report.errors if "Invalid predicate" in e.message]
        assert len(errors) == 1

    def test_invalid_curie_format(self, tmp_data_dir):
        tsv = _write_tsv(
            tmp_data_dir / "chemicals" / "chemical_mappings.tsv",
            """\
            subject_label\tobject_id\tobject_label\tobject_source\tpredicate_id
            glucose\tNOCOLON\tglucose\tCHEBI\tskos:exactMatch
            """,
        )
        report = ValidationReport()
        validate_tsv(tsv, report)
        errors = [e for e in report.errors if "Invalid CURIE" in e.message]
        assert len(errors) == 1

    def test_header_only_file(self, tmp_data_dir):
        tsv = _write_tsv(
            tmp_data_dir / "chemicals" / "chemical_mappings.tsv",
            """\
            subject_label\tobject_id\tobject_label\tobject_source\tpredicate_id
            """,
        )
        report = ValidationReport()
        validate_tsv(tsv, report)
        assert report.ok


class TestNegativeMappingValidation:
    """Negative mapping TSV validation."""

    def test_valid_negative(self, tmp_data_dir):
        header = (
            "subject_label\trejected_object_id\trejected_object_label\t"
            "correct_object_id\tcorrect_object_label\trejection_reason\t"
            "provenance\treported_date\treporter"
        )
        row = (
            "casamino acids\tCHEBI:78020\theptacosanoate\t"
            "MICRO:0000184\tcasamino acids\tLLM hallucinated CURIE\t"
            "CultureBotAI/MicroMediaParam\t2026-02-19\tturbomam"
        )
        tsv_path = tmp_data_dir / "chemicals" / "chemical_negative_mappings.tsv"
        tsv_path.write_text(f"{header}\n{row}\n", encoding="utf-8")
        report = ValidationReport()
        validate_tsv(tsv_path, report)
        assert report.ok


class TestDirectoryValidation:
    """Directory-level validation."""

    def test_no_tsv_files(self, tmp_path):
        report = validate_directory(tmp_path)
        assert not report.ok
        assert any("No TSV files" in e.message for e in report.errors)

    def test_valid_directory(self, tmp_data_dir):
        _write_tsv(
            tmp_data_dir / "chemicals" / "chemical_mappings.tsv",
            """\
            subject_label\tobject_id\tobject_label\tobject_source\tpredicate_id
            """,
        )
        report = validate_directory(tmp_data_dir)
        assert report.ok
