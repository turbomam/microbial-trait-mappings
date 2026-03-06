# Microbial Trait Mappings — justfile
# Run `just` to see all available targets.

data_dir := "data"
conf_dir := "conf"
oak_config := conf_dir / "oak_config.yaml"

# List available targets
default:
    @just --list

# Run all tests
test:
    uv run pytest -v

# Run only conversion pattern tests
test-patterns:
    uv run pytest -v tests/test_conversion_patterns.py

# Run only round-trip edge resolution tests
test-round-trip:
    uv run pytest -v tests/test_round_trip.py

# Run only data integrity tests (what CI runs)
test-data:
    uv run pytest -v tests/test_data_integrity.py

# Validate TSV column schemas
validate:
    uv run mtm-validate --input-dir {{data_dir}}

# Check normalization consistency
normalize-check:
    uv run mtm-normalize --check --input-dir {{data_dir}} --strict

# Full audit: validate + build-schema + verify + normalize-check
audit:
    uv run mtm-audit --input-dir {{data_dir}} --oak-config {{oak_config}}

# Lint and format check
lint:
    uv run ruff check .
    uv run ruff format --check .

# Fix lint and formatting issues
fix:
    uv run ruff check --fix .
    uv run ruff format .

# Round trip: validate → test-patterns → test-round-trip → normalize-check
round-trip: validate test-patterns test-round-trip normalize-check
    @echo "Round trip passed: all mapping patterns valid and edges resolve correctly."

# Full CI check: everything that should pass before committing
ci: lint validate test round-trip
    @echo "All CI checks passed."

# Clean generated artifacts
clean:
    rm -rf generated/ cache/ .pytest_cache/ .mypy_cache/ .ruff_cache/
