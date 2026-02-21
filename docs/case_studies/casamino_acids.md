# Case Study: Casamino Acids → CHEBI:78020

## Summary

An LLM-generated mapping assigned "casamino acids" to **CHEBI:78020** (heptacosanoate, a C27 fatty acid anion with formula C27H53O2). This is completely wrong. Casamino acids is a complex biological mixture produced by acid hydrolysis of casein — it is not a single molecule and has no CHEBI representation.

The error originated in the CultureBotAI/MicroMediaParam repository, propagated into KG-Microbe's MediaDive transform, and affected 57 rows and dozens of knowledge graph edges.

## The Error

| Field | Value |
|-------|-------|
| Compound name | Casamino acids |
| Assigned CURIE | CHEBI:78020 |
| Actual CHEBI:78020 label | heptacosanoate |
| CHEBI:78020 formula | C27H53O2 |
| Rows affected | 57 in compound_mappings_strict_hydrate.tsv |
| Edges affected | Dozens of `biolink:has_part` edges in transformed output |

The mapping file's own columns showed the mismatch side by side:

```
original          mapped        chebi_label      chebi_formula
Casamino acids    CHEBI:78020   heptacosanoate   C27H53O2
```

## What Is Casamino Acids?

Casamino acids is a standard microbiological medium supplement produced by acid hydrolysis of casein (milk protein). It provides free amino acids and small peptides. It is a mixture, not a single molecule.

### Ontology Representation

| Ontology | Term ID | Label | Notes |
|----------|---------|-------|-------|
| **CHEBI** | (none) | — | No CHEBI term exists. CHEBI models individual chemicals. |
| **MicrO** | MICRO:0000184 | casamino acids | Correct term. "An acid hydrolysate of casein." |
| **MCO** | MCO:0000081 | vitamin assay casamino acids | Vitamin-depleted variant. |
| **FOODON** | FOODON:03315719 | mammalian milk protein (hydrolyzed) | Closest FOODON term, not exact. |

The correct CURIE is **MICRO:0000184**.

## How the Error Occurred

1. An LLM (Claude) was used to generate CHEBI mappings for media compounds in CultureBotAI/MicroMediaParam (commit f02b23c1, 2025-10-29).
2. The LLM fabricated CHEBI:78020 as a mapping for casamino acids. The code comment "if exists, else use peptone" and `confidence="medium"` indicate the LLM was uncertain but guessed anyway.
3. MicroMediaParam's own validation pipeline detected the label mismatch and marked it as `NOT_FOUND`. The finding was recorded but never corrected.
4. KG-Microbe downloaded the mapping file and used it in the MediaDive transform, creating incorrect knowledge graph edges.

## Lessons

1. **Never trust LLM-generated CURIEs without label verification.** The single most important check: after assigning a CURIE, verify that the source ontology's canonical label matches what you think it is.

2. **Complex biological mixtures don't belong in CHEBI.** Trying to force casamino acids into CHEBI guarantees failure because there is no correct CHEBI ID. Use MICRO or FOODON for mixture terms.

3. **Validation findings need action.** Detection is necessary but not sufficient. The upstream pipeline caught the error and did nothing.

4. **Negative mappings prevent recurrence.** This error is now recorded in `data/chemicals/chemical_negative_mappings.tsv` so that no future mapping attempt can reintroduce CHEBI:78020 for casamino acids.
