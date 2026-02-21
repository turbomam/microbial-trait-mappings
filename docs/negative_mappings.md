# Negative Mappings

## What Are Negative Mappings?

A negative mapping is an explicit record that a particular string-to-CURIE association is **wrong**. It states: "Label X is NOT entity Y."

## Why Track Negative Mappings?

1. **Prevent reintroduction.** Without negative tracking, the same wrong mapping can be independently rediscovered and reintroduced by different people or tools. An LLM asked to map "casamino acids" to CHEBI will likely produce the same wrong answer every time.

2. **Document provenance of errors.** Knowing where a bad mapping came from helps audit other mappings from the same source.

3. **Guide correct alternatives.** When a negative mapping includes the correct CURIE, it serves as a redirect.

4. **Support automated QC.** CI can check that no positive mapping duplicates a known negative mapping.

## Negative Mapping File Format

Each entity-type directory contains a `*_negative_mappings.tsv` file with these columns:

| Column | Required | Description |
|--------|----------|-------------|
| `subject_label` | yes | The label that was incorrectly mapped |
| `rejected_object_id` | yes | The wrong CURIE |
| `rejected_object_label` | yes | What the rejected CURIE actually represents |
| `correct_object_id` | no | The correct CURIE, if known |
| `correct_object_label` | no | Label of the correct CURIE |
| `rejection_reason` | yes | Why this mapping is wrong |
| `provenance` | no | Where the bad mapping was found (repo, file, commit) |
| `reported_date` | yes | ISO-8601 date when the error was identified |
| `reporter` | no | Who reported the error (ORCID or GitHub handle) |

## When to Create a Negative Mapping

Create a negative mapping when:

- You discover an incorrect CURIE assignment in any upstream data source
- An LLM generates a CURIE that doesn't match on label verification
- A CURIE is structurally valid but semantically wrong (e.g., CHEBI:78020 is a real CHEBI term, but it's heptacosanoate, not casamino acids)
- A mapping was once correct but the ontology term has been obsoleted or merged

## Example

The canonical example is the casamino acids / CHEBI:78020 error documented in [`case_studies/casamino_acids.md`](case_studies/casamino_acids.md):

```tsv
subject_label	rejected_object_id	rejected_object_label	correct_object_id	correct_object_label	rejection_reason	provenance	reported_date	reporter
casamino acids	CHEBI:78020	heptacosanoate	MICRO:0000184	casamino acids	LLM-hallucinated CURIE...	CultureBotAI/MicroMediaParam...	2026-02-19	turbomam
```

## Relationship to Positive Mappings

- A (subject_label, object_id) pair must never appear in both the positive and negative mapping files for the same category.
- CI tests enforce this constraint.
- If a positive mapping is discovered to be wrong, it should be moved to the negative file with a rejection reason, and optionally replaced with the correct mapping in the positive file.
