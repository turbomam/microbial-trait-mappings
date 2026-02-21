# Data Dictionary

This directory contains curated string-to-CURIE mappings organized by entity type.

## Directory Structure

```
data/
├── chemicals/
│   ├── chemical_mappings.tsv              # Positive: compound name → CHEBI/MICRO/FOODON CURIE
│   └── chemical_negative_mappings.tsv     # Negative: known-wrong mappings
├── enzymes/
│   ├── enzyme_mappings.tsv                # Positive: enzyme name → EC number
│   └── enzyme_negative_mappings.tsv
├── pathways/
│   ├── pathway_mappings.tsv               # Positive: pathway name → GO CURIE
│   └── pathway_negative_mappings.tsv
└── phenotypes/
    ├── phenotype_mappings.tsv             # Positive: phenotype label → OMP/PATO CURIE
    └── phenotype_negative_mappings.tsv
```

## Positive Mapping Schema

| Column | Required | Description |
|--------|----------|-------------|
| `subject_label` | yes | Raw free-text label from source data |
| `subject_label_normalized` | auto | Output of `normalize_text()` — filled by tooling |
| `object_id` | yes | Authoritative ontology CURIE (e.g., CHEBI:17234) |
| `object_label` | yes | Canonical label from the source ontology |
| `object_source` | yes | Prefix of the source ontology (e.g., CHEBI, GO, EC) |
| `predicate_id` | yes | SKOS mapping predicate (skos:exactMatch, skos:closeMatch, skos:broadMatch, skos:narrowMatch, skos:relatedMatch) |
| `confidence` | no | Confidence score 0.0–1.0 |
| `mapping_justification` | no | SEMAPV term for how the mapping was derived |
| `curator` | no | ORCID or GitHub handle of the curator |
| `source_dataset` | no | Origin dataset (mediadive, bacdive, madin, metatraits) |
| `notes` | no | Free text notes |
| `verified_date` | no | ISO-8601 date of last OAK verification |

## Negative Mapping Schema

Negative mappings record known-wrong associations so they are never reintroduced.

| Column | Required | Description |
|--------|----------|-------------|
| `subject_label` | yes | The label that was incorrectly mapped |
| `rejected_object_id` | yes | The wrong CURIE |
| `rejected_object_label` | yes | What the rejected CURIE actually represents |
| `correct_object_id` | no | The correct CURIE, if known |
| `correct_object_label` | no | Label of the correct CURIE |
| `rejection_reason` | yes | Why this mapping is wrong |
| `provenance` | no | Where the bad mapping was found |
| `reported_date` | yes | ISO-8601 date when the error was identified |
| `reporter` | no | Who reported the error |

## Predicate Vocabulary

| Predicate | Meaning |
|-----------|---------|
| `skos:exactMatch` | The subject label means exactly the same thing as the object term |
| `skos:closeMatch` | Very similar but not identical (e.g., different salt forms) |
| `skos:broadMatch` | The object term is broader than the subject label |
| `skos:narrowMatch` | The object term is narrower than the subject label |
| `skos:relatedMatch` | Related but not hierarchically |
