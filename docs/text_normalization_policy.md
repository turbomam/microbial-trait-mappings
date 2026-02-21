# Text Normalization Policy

## Purpose

Free-text trait labels from different sources use inconsistent representations of the same compound, enzyme, or pathway. This policy codifies how labels are normalized to canonical forms so that variant spellings converge to a single lookup key.

## Normalization Pipeline

The `normalize_text()` function applies these transformations in order:

### 1. Unicode NFC Normalization

All text is first normalized to Unicode NFC form. This ensures that composed and decomposed representations of accented characters are treated identically.

### 2. Greek Letters → ASCII

Greek letters are replaced with their English names. Hyphens are inserted at word boundaries to maintain readability.

| Input | Output |
|-------|--------|
| α-D-glucose | alpha-D-glucose |
| β-galactosidase | beta-galactosidase |
| γ-aminobutyric acid | gamma-aminobutyric acid |
| Δ9-THC | Delta-9-THC |

The micro sign (U+00B5, `µ`) and Greek mu (U+03BC, `μ`) both normalize to "mu".

**Full mapping:** All 24 Greek lowercase letters (including final sigma ς) and their uppercase variants are mapped.

### 3. Subscript/Superscript Digits → Plain ASCII

Unicode subscript and superscript characters are replaced with their plain ASCII equivalents.

| Input | Output |
|-------|--------|
| H₂O | H2O |
| Fe³⁺ | Fe3+ |
| CO₂ | CO2 |

### 4. Whitespace Collapse

Multiple whitespace characters (spaces, tabs, newlines) are collapsed to a single space. Leading and trailing whitespace is stripped.

### 5. Stereochemistry Optical Rotation Strip

Optical rotation prefixes are removed:

| Input | Output |
|-------|--------|
| (+)-D-glucose | D-glucose |
| (-)-arabinose | arabinose |
| (±)-camphor | camphor |

This step is optional and can be disabled with `strip_stereo=False`.

**Rationale:** Optical rotation signs are measurement artifacts, not structural identifiers. Most trait databases do not distinguish (+)- and (-)-forms, and including them causes false non-matches.

### 6. Lowercase

All text is converted to lowercase.

This step is optional and can be disabled with `lowercase=False`.

## Convergence Examples

These variant representations all normalize to the same canonical form:

| Variants | Canonical Form |
|----------|---------------|
| α-D-glucose, alpha-D-glucose, α-D-Glucose, Alpha-D-Glucose | alpha-d-glucose |
| H₂O, H2O, h2o | h2o |
| (+)-D-arabitol, D-arabitol, d-arabitol | d-arabitol |
| β-galactosidase, Beta-galactosidase, β-Galactosidase | beta-galactosidase |

## When Normalization Is Applied

- The `subject_label_normalized` column in positive mapping TSVs is filled by `mtm-normalize`
- Normalization consistency is checked by `mtm-normalize --check`
- CI enforces that committed `subject_label_normalized` values match `normalize_text(subject_label)`

## Limitations

- Chemical structure (SMILES, InChI) is not normalized — this is for text labels only
- Synonym expansion is out of scope — "vitamin C" and "ascorbic acid" remain distinct
- Language translation is out of scope — only English labels are supported
