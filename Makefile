# Microbial Trait Mappings - Makefile
#
# Convention: targets produce files; .PHONY only for workflow commands.
# Uses $< (first prerequisite) and $@ (target) per project standards.

DATA_DIR := data
CONF_DIR := conf
GENERATED_DIR := generated
OAK_CONFIG := $(CONF_DIR)/oak_config.yaml

CHEMICAL_MAPPINGS := $(DATA_DIR)/chemicals/chemical_mappings.tsv
ENZYME_MAPPINGS := $(DATA_DIR)/enzymes/enzyme_mappings.tsv
PATHWAY_MAPPINGS := $(DATA_DIR)/pathways/pathway_mappings.tsv
PHENOTYPE_MAPPINGS := $(DATA_DIR)/phenotypes/phenotype_mappings.tsv

ALL_MAPPINGS := $(CHEMICAL_MAPPINGS) $(ENZYME_MAPPINGS) $(PATHWAY_MAPPINGS) $(PHENOTYPE_MAPPINGS)

VALIDATION_SCHEMA := $(GENERATED_DIR)/validation_schema.yaml

# ── Validation ──────────────────────────────────────────────────────────────

$(VALIDATION_SCHEMA): $(ALL_MAPPINGS) microbial_trait_mappings/verify.py
	mkdir -p $(GENERATED_DIR)
	uv run mtm-build-schema --input-dir $(DATA_DIR) --output $@

# ── Workflow targets ────────────────────────────────────────────────────────

.PHONY: validate normalize-check build-schema verify audit test lint clean

validate:
	uv run mtm-validate --input-dir $(DATA_DIR)

normalize-check:
	uv run mtm-normalize --check --input-dir $(DATA_DIR) --strict

build-schema: $(VALIDATION_SCHEMA)

verify: $(VALIDATION_SCHEMA)
	uv run mtm-verify --input-dir $(DATA_DIR) --oak-config $(OAK_CONFIG)

audit:
	uv run mtm-audit --input-dir $(DATA_DIR) --oak-config $(OAK_CONFIG)

test:
	uv run pytest -v

lint:
	uv run ruff check .
	uv run ruff format --check .

clean:
	rm -rf $(GENERATED_DIR) cache/ .pytest_cache/ .mypy_cache/ .ruff_cache/
