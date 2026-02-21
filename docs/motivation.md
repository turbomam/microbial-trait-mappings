# Motivation

## The String-to-Thing Problem

Microbial trait databases store information about what microbes do — what chemicals they consume, what enzymes they produce, what pathways they use, what phenotypes they exhibit. These traits are typically recorded as free-text labels: "glucose", "α-D-galactose", "catalase", "glycolysis".

To integrate this data into knowledge graphs or perform cross-database comparisons, these free-text labels must be mapped to authoritative ontology identifiers (CURIEs). "glucose" becomes `CHEBI:17234`. "glycolysis" becomes `GO:0006096`. This is the string-to-thing mapping problem.

## Why Existing Artifacts Are Insufficient

Mapping artifacts for the KG-Microbe / METPO / CultureBot ecosystem have accumulated organically across multiple repositories:

1. **Format inconsistency** — Mappings exist as YAML dictionaries, JSON objects, TSV files, and SSSOM TSVs across different repos. No single schema governs them all.

2. **No systematic verification** — CURIEs are assigned (often by LLMs or manual lookup) but rarely verified against the source ontology afterward. When a CHEBI ID is assigned, nobody routinely checks whether the canonical CHEBI label matches the intended compound.

3. **No negative tracking** — When a mapping is discovered to be wrong, there is no mechanism to record this fact and prevent the same error from being reintroduced. Bad mappings propagate silently.

4. **No text normalization** — Different representations of the same compound ("α-D-glucose" vs "alpha-D-glucose" vs "α-d-glucose") are treated as different lookup keys, leading to missed matches and duplicate entries.

5. **Duplicated data** — The same mapping data is copied into multiple repositories, creating divergent versions that drift over time.

## What This Repository Provides

This repository is a **practical working tool** — not a standards proposal. It provides:

### Methodology
- A codified **text normalization pipeline** for microbial trait labels
- A **CURIE verification workflow** using OAK and linkml-term-validator
- A **negative mapping format** for recording and preventing known-wrong associations
- **CI enforcement** so that data quality checks run on every PR

### Curated Data
- **Positive mappings** — verified string-to-CURIE associations organized by entity type
- **Negative mappings** — explicit records of wrong CURIEs with rejection reasons and correct alternatives
- **Data provenance** — every mapping tracks its source dataset, curator, and verification date

### Relationship to SSSOM

[SSSOM](https://github.com/mapping-commons/sssom) (Simple Standard for Sharing Ontological Mappings) is a community standard for CURIE-to-CURIE mappings (e.g., CHEBI:17234 ↔ KEGG:C00031). This repo focuses on **string-to-CURIE** mappings — the upstream step of resolving free-text labels to their first ontology identifier. The two are complementary:

1. This repo maps "glucose" → `CHEBI:17234` (string → thing)
2. SSSOM maps `CHEBI:17234` ↔ `KEGG:C00031` (thing ↔ thing)

## Design Decisions

- **TSV format** — Simple, diff-friendly, editable in spreadsheets. No special tooling needed to read or contribute.
- **Separate negative mapping files** — Negative knowledge is first-class data, not comments or issue threads.
- **Entity-type directories** — Chemicals, enzymes, pathways, and phenotypes have different ontology authorities and different normalization challenges. Separating them keeps files manageable.
- **Verification via OAK** — OAK provides a uniform interface to OBO Foundry ontologies via local SQLite databases. This is faster and more reliable than web API calls.
- **Click CLIs with pyproject.toml entries** — Every tool is a proper CLI command, not a loose script.
