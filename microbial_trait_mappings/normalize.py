"""Text normalization pipeline for microbial trait labels.

Handles Greek letters, subscripts/superscripts, stereochemistry notation,
and whitespace so that variant spellings of the same compound converge to
a single canonical form.
"""

from __future__ import annotations

import re
import unicodedata

# Greek lower-case → ASCII
GREEK_TO_ASCII: dict[str, str] = {
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "ε": "epsilon",
    "ζ": "zeta",
    "η": "eta",
    "θ": "theta",
    "ι": "iota",
    "κ": "kappa",
    "λ": "lambda",
    "μ": "mu",
    "ν": "nu",
    "ξ": "xi",
    "ο": "omicron",
    "π": "pi",
    "ρ": "rho",
    "σ": "sigma",
    "ς": "sigma",  # final sigma
    "τ": "tau",
    "υ": "upsilon",
    "φ": "phi",
    "χ": "chi",
    "ψ": "psi",
    "ω": "omega",
}

# Add upper-case variants
GREEK_TO_ASCII.update({k.upper(): v.capitalize() for k, v in GREEK_TO_ASCII.items() if k != "ς"})

# Unicode subscript → plain ASCII
SUBSCRIPT_MAP: dict[str, str] = {
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
    "₊": "+",
    "₋": "-",
    "₌": "=",
    "₍": "(",
    "₎": ")",
}

# Unicode superscript → plain ASCII
SUPERSCRIPT_MAP: dict[str, str] = {
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "⁺": "+",
    "⁻": "-",
    "⁼": "=",
    "⁽": "(",
    "⁾": ")",
}

# Micro sign (U+00B5) vs Greek mu (U+03BC) — both should normalize the same
_MICRO_SIGN = "\u00b5"

# Optical-rotation prefix pattern: (+)-, (-)-, (±)-
_STEREO_PREFIX_RE = re.compile(r"\([\+\-±]\)-")

# Build a single translation table for subscripts + superscripts
_SUB_SUPER_TABLE = str.maketrans({**SUBSCRIPT_MAP, **SUPERSCRIPT_MAP})


def _replace_greek(text: str) -> str:
    """Replace Greek letters with ASCII equivalents, inserting hyphens at word boundaries."""
    # Replace micro sign (U+00B5) with Greek mu (U+03BC) so it gets the same treatment
    text = text.replace(_MICRO_SIGN, "μ")

    result: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in GREEK_TO_ASCII:
            ascii_val = GREEK_TO_ASCII[ch]
            # Insert hyphen before if previous char is alphanumeric
            if result and result[-1].isalnum():
                result.append("-")
            result.append(ascii_val)
            # Insert hyphen after if next char is alphanumeric
            if i + 1 < len(text) and text[i + 1].isalnum():
                result.append("-")
            i += 1
        else:
            result.append(ch)
            i += 1
    return "".join(result)


def normalize_text(
    value: str,
    *,
    lowercase: bool = True,
    strip_stereo: bool = True,
) -> str:
    """Normalize a free-text label to a canonical form.

    Pipeline:
        1. Unicode NFC normalization
        2. Greek letters → ASCII with hyphen insertion
        3. Subscript/superscript digits → plain ASCII
        4. Whitespace collapse
        5. Stereochemistry optical rotation strip (optional)
        6. Lowercase (optional)

    Args:
        value: Raw free-text label.
        lowercase: Convert to lowercase (default True).
        strip_stereo: Remove optical rotation prefixes like (+)- (default True).

    Returns:
        Normalized string.
    """
    if not value:
        return ""

    # 1. Unicode NFC
    text = unicodedata.normalize("NFC", value.strip())

    # 2. Greek → ASCII
    text = _replace_greek(text)

    # 3. Subscripts / superscripts → plain ASCII
    text = text.translate(_SUB_SUPER_TABLE)

    # 4. Whitespace collapse
    text = " ".join(text.split())

    # 5. Strip stereochemistry optical rotation
    if strip_stereo:
        text = _STEREO_PREFIX_RE.sub("", text)

    # 6. Lowercase
    if lowercase:
        text = text.lower()

    return text.strip()
