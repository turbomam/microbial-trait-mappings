# CURIE Namespace Policy

## Preferred Ontology per Entity Type

Each entity type has a preferred ontology authority. When multiple ontologies cover a term, prefer the one listed first:

### Chemicals / Substrates

| Priority | Ontology | Scope | Notes |
|----------|----------|-------|-------|
| 1 | **CHEBI** | Individual chemical entities | Primary authority for small molecules |
| 2 | **MICRO** (MicrO) | Microbiological media components | For complex mixtures (casamino acids, peptone, tryptone) that CHEBI does not cover |
| 3 | **FOODON** | Food-derived compounds | When neither CHEBI nor MICRO has a term |
| 4 | **KEGG** (compound) | Metabolites | Use as fallback; prefer CHEBI when both exist |
| 5 | **PubChem** (CID) | Any chemical | Last resort; lacks ontological structure |

**Do not use CHEBI for complex biological mixtures.** Casamino acids, peptone, yeast extract, and similar media components are mixtures, not molecules. Forcing them into CHEBI leads to hallucinated or wrong CURIEs. Use MICRO or FOODON instead.

### Enzymes

| Priority | Ontology | Scope | Notes |
|----------|----------|-------|-------|
| 1 | **EC** | Enzyme Commission numbers | Canonical enzyme classification |
| 2 | **GO** (molecular function) | Enzyme activities | When EC number is unavailable |

### Pathways / Biological Processes

| Priority | Ontology | Scope | Notes |
|----------|----------|-------|-------|
| 1 | **GO** (biological process) | Metabolic and signaling pathways | Primary authority |
| 2 | **KEGG** (pathway) | Pathway maps | Use KEGG pathway IDs as fallback |

### Phenotypes / Traits

| Priority | Ontology | Scope | Notes |
|----------|----------|-------|-------|
| 1 | **OMP** | Microbial phenotypes | Primary for prokaryotic phenotypes |
| 2 | **PATO** | Phenotypic qualities | For generic qualities (shape, size, color) |
| 3 | **MICRO** | Microbiological characteristics | For culture-specific traits |
| 4 | **ENVO** | Environmental features | For habitat/isolation-source phenotypes |

## CURIE Format

All CURIEs must use the standard `PREFIX:LOCAL_ID` format:

- `CHEBI:17234` (not `http://purl.obolibrary.org/obo/CHEBI_17234`)
- `GO:0006096` (not `GO_0006096`)
- `EC:1.1.1.1` (not `EC 1.1.1.1`)
- `MICRO:0000184` (not `micro:0000184`)

## Verification Requirements

Every CURIE in a positive mapping must be verified against its source ontology:

1. The CURIE must resolve to a term in the source ontology (not obsolete)
2. The `object_label` must match the canonical label from the source ontology (case-insensitive)
3. For OBO Foundry ontologies: verification uses OAK with `sqlite:obo:X` adapters
4. For non-OBO identifiers (EC, PubChem, CAS-RN): verification uses the SRI Node Normalizer

## When No Good CURIE Exists

If no authoritative CURIE exists for a label:

1. **Do not fabricate one.** Do not guess CHEBI IDs or use LLM-generated CURIEs without verification.
2. Record the label in the mapping TSV with an empty `object_id` and a note explaining the gap.
3. Consider whether the term belongs in METPO (for ontology-level gaps) or should be requested from the relevant ontology.
