# Microbial Trait Mappings - Development Guide for Claude Code

## Project Overview

Curated string-to-CURIE mappings and verification tools for microbial trait labels.
Maps free-text compound/pathway/enzyme/phenotype names to authoritative ontology CURIEs
(CHEBI, GO, EC, OMP, MICRO, FOODON, ENVO) with automated verification via OAK and
linkml-term-validator.

## Build & Test

```bash
uv sync                              # Install dependencies
uv run pytest -v                     # Run tests
uv run ruff check .                  # Lint
uv run ruff format --check .         # Format check
uv run mtm-validate --input-dir data/   # Validate TSV schemas
uv run mtm-normalize --check --input-dir data/ --strict  # Normalization check
uv run mtm-audit --input-dir data/ --oak-config conf/oak_config.yaml  # Full audit
```

## CLI Tools (all prefixed `mtm-`)

| Command | Purpose |
|---------|---------|
| `mtm-normalize` | Normalize labels or check normalization consistency |
| `mtm-build-schema` | Generate LinkML validation schema from mapping TSVs |
| `mtm-verify` | Verify CURIEs via linkml-term-validator / OAK |
| `mtm-validate` | Validate mapping TSV column schemas |
| `mtm-audit` | Full audit (validate + build-schema + verify + normalize-check) |
| `mtm-sri-normalize` | Normalize CURIEs via SRI Node Normalizer |

## Directory Structure

- `data/` — curated TSV mapping files (chemicals, enzymes, pathways, phenotypes)
- `conf/` — OAK adapter configuration
- `microbial_trait_mappings/` — Python package
- `tests/` — pytest tests (including data integrity tests run on every PR)
- `docs/` — policy documentation and case studies
- `generated/` — build artifacts (.gitignore'd except .gitkeep)

## Adding New Mappings

1. Add rows to the appropriate `data/<category>/<category>_mappings.tsv`
2. Fill required columns: `subject_label`, `object_id`, `object_label`, `object_source`, `predicate_id`
3. Run `uv run mtm-validate --input-dir data/` to check column schema
4. Run `uv run mtm-normalize --check --input-dir data/` to verify normalization
5. Run `uv run mtm-audit --input-dir data/ --oak-config conf/oak_config.yaml` for full verification

## Script Standards

All scripts use Click CLIs, have pyproject.toml entries, and follow the pattern:
```python
@click.command()
@click.option('--input-dir', '-i', required=True, type=click.Path(exists=True))
def main(input_dir: str):
    """Description."""
    pass
```
