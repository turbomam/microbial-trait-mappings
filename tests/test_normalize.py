"""Tests for the text normalization pipeline."""

from microbial_trait_mappings.normalize import (
    GREEK_TO_ASCII,
    SUBSCRIPT_MAP,
    SUPERSCRIPT_MAP,
    normalize_text,
)


class TestGreekConversion:
    """Greek letter → ASCII conversion."""

    def test_alpha(self):
        assert normalize_text("α-D-glucose") == "alpha-d-glucose"

    def test_beta(self):
        assert normalize_text("β-galactosidase") == "beta-galactosidase"

    def test_gamma(self):
        assert normalize_text("γ-aminobutyric acid") == "gamma-aminobutyric acid"

    def test_upper_greek(self):
        assert normalize_text("Δ9-THC", lowercase=False) == "Delta-9-THC"

    def test_all_lower_greek_mapped(self):
        """Every lower-case Greek letter should have a mapping."""
        lower_greek = "αβγδεζηθικλμνξοπρστυφχψω"
        for ch in lower_greek:
            assert ch in GREEK_TO_ASCII, f"Missing mapping for {ch}"

    def test_micro_sign(self):
        """µ (U+00B5 micro sign) should normalize same as μ (U+03BC Greek mu)."""
        assert normalize_text("\u00b5m") == normalize_text("μm")

    def test_hyphen_insertion_before_greek(self):
        """Hyphen inserted between alphanumeric and Greek replacement."""
        assert normalize_text("D-α-glucose") == "d-alpha-glucose"

    def test_no_double_hyphen(self):
        """Hyphens around Greek letters should not double up."""
        result = normalize_text("α-D-glucose")
        assert "--" not in result


class TestSubscriptSuperscript:
    """Unicode sub/superscript → ASCII conversion."""

    def test_subscript_digits(self):
        assert normalize_text("H₂O") == "h2o"

    def test_superscript_digits(self):
        assert normalize_text("Fe³⁺") == "fe3+"

    def test_subscript_map_complete(self):
        for i in range(10):
            assert chr(0x2080 + i) in SUBSCRIPT_MAP

    def test_superscript_map_has_common_digits(self):
        assert "²" in SUPERSCRIPT_MAP
        assert "³" in SUPERSCRIPT_MAP


class TestStereochemistry:
    """Optical rotation prefix stripping."""

    def test_strip_plus_rotation(self):
        assert normalize_text("(+)-D-glucose") == "d-glucose"

    def test_strip_minus_rotation(self):
        assert normalize_text("(-)-arabinose") == "arabinose"

    def test_strip_plusminus_rotation(self):
        assert normalize_text("(±)-camphor") == "camphor"

    def test_preserve_when_disabled(self):
        assert normalize_text("(+)-D-glucose", strip_stereo=False) == "(+)-d-glucose"


class TestWhitespace:
    """Whitespace handling."""

    def test_collapse_multiple_spaces(self):
        assert normalize_text("amino   butyric   acid") == "amino butyric acid"

    def test_strip_leading_trailing(self):
        assert normalize_text("  glucose  ") == "glucose"

    def test_tabs_and_newlines(self):
        assert normalize_text("amino\tbutyric\nacid") == "amino butyric acid"


class TestLowercase:
    """Case handling."""

    def test_lowercase_default(self):
        assert normalize_text("D-Glucose") == "d-glucose"

    def test_preserve_case(self):
        assert normalize_text("D-Glucose", lowercase=False) == "D-Glucose"


class TestEdgeCases:
    """Edge cases."""

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_none_like_empty(self):
        assert normalize_text("   ") == ""

    def test_already_normalized(self):
        text = "alpha-d-glucose"
        assert normalize_text(text) == text

    def test_combined_pipeline(self):
        """Full pipeline: Greek + subscript + stereo + lowercase + whitespace."""
        result = normalize_text("  (+)-α-D-Glucose₆  ")
        assert result == "alpha-d-glucose6"


class TestConvergence:
    """Different representations of the same compound should converge."""

    def test_alpha_d_glucose_variants(self):
        variants = [
            "α-D-glucose",
            "alpha-D-glucose",
            "α-D-Glucose",
            "  α-D-glucose  ",
        ]
        normalized = {normalize_text(v) for v in variants}
        assert len(normalized) == 1, f"Non-convergent: {normalized}"

    def test_h2o_variants(self):
        variants = ["H₂O", "H2O", "h2o"]
        normalized = {normalize_text(v) for v in variants}
        assert len(normalized) == 1, f"Non-convergent: {normalized}"
