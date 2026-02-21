# Microbial Trait Mappings

Curated string-to-CURIE mappings and verification tools for microbial trait labels.

## Problem

Microbial trait databases (BacDive, MediaDive, Madin et al., MetaTraits) use free-text labels for chemicals, enzymes, pathways, and phenotypes. Converting these labels to authoritative ontology identifiers (CURIEs) is essential for knowledge graph construction, but the mapping artifacts are:

- **Scattered** across multiple repositories in inconsistent formats (YAML, JSON, TSV, SSSOM)
- **Unverified** — assigned CURIEs are not routinely checked against their source ontologies
- **Missing negative tracking** — no mechanism to record and prevent known-wrong mappings
- **Not normalized** — variant spellings (α-D-glucose vs alpha-D-glucose) are treated as different keys

This repo consolidates and replaces mapping data previously scattered across multiple repositories.

## Solution

This repository provides:

1. **Curated TSV files** mapping free-text labels to ontology CURIEs, organized by entity type (chemicals, enzymes, pathways, phenotypes)
2. **Negative mappings** — explicit records of known-wrong CURIE assignments so they are never reintroduced
3. **Text normalization** — a codified pipeline for canonicalizing Greek letters, subscripts, stereochemistry notation, and whitespace
4. **Automated verification** — every CURIE is verified against its source ontology via [OAK](https://github.com/INCATools/ontology-access-kit) and [linkml-term-validator](https://github.com/INCATools/linkml-term-validator)
5. **CI enforcement** — all checks run on every PR

## Quick Start

```bash
# Install
git clone https://github.com/turbomam/microbial-trait-mappings.git
cd microbial-trait-mappings
uv sync

# Validate TSV column schemas
uv run mtm-validate --input-dir data/

# Check text normalization consistency
uv run mtm-normalize --check --input-dir data/

# Full audit (validate + normalize + build schema + verify CURIEs)
uv run mtm-audit --input-dir data/ --oak-config conf/oak_config.yaml

# Run tests
uv run pytest -v
```

## CLI Tools

All commands are prefixed with `mtm-`:

| Command | Purpose |
|---------|---------|
| `mtm-normalize` | Normalize trait labels or check consistency |
| `mtm-build-schema` | Generate LinkML validation schema from mapping TSVs |
| `mtm-verify` | Verify CURIEs against source ontologies via OAK |
| `mtm-validate` | Validate mapping TSV column schemas |
| `mtm-audit` | Full audit (all of the above) |
| `mtm-sri-normalize` | Normalize CURIEs via SRI Node Normalizer |

## Data Organization

```
data/
├── chemicals/         # Compound names → CHEBI, MICRO, FOODON CURIEs
├── enzymes/           # Enzyme names → EC numbers
├── pathways/          # Pathway names → GO CURIEs
└── phenotypes/        # Phenotype labels → OMP, PATO CURIEs
```

Each category has:
- `*_mappings.tsv` — verified positive mappings
- `*_negative_mappings.tsv` — known-wrong mappings with rejection reasons

See [`data/README.md`](data/README.md) for the full column schema.

## Documentation

- [`docs/motivation.md`](docs/motivation.md) — Why this repo exists
- [`docs/text_normalization_policy.md`](docs/text_normalization_policy.md) — Normalization rules
- [`docs/curie_namespace_policy.md`](docs/curie_namespace_policy.md) — Preferred ontology per entity type
- [`docs/negative_mappings.md`](docs/negative_mappings.md) — How negative mappings work
- [`docs/case_studies/casamino_acids.md`](docs/case_studies/casamino_acids.md) — Canonical error case study

## Related Projects

- [METPO](https://github.com/berkeleybop/metpo) — Microbial Ecophysiological Trait and Phenotype Ontology
- [KG-Microbe](https://github.com/berkeleybop/kg-microbe) — Knowledge graph integrating microbial trait data
- [SSSOM](https://github.com/mapping-commons/sssom) — Simple Standard for Sharing Ontological Mappings (complementary standard for CURIE-to-CURIE mappings)

## License

[CC-BY-4.0](LICENSE)
