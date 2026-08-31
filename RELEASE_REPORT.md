# Nutrition Tracking System Upgrade — Release Report (0.4.0)

## Baseline

- Repository: `actowery/fitness-ledger`
- Release: `0.4.0`
- Baseline test result: 68 passed, 0 failed
- Canonical personal artifacts: Library-backed ledger JSON, current-state cache, and workbook; not present in this public repository
- Repository artifacts: Library-native skills, offline tracker, fitness reconciliation helpers, schemas, fixtures, and regression tests
- Canonical rules preserved: JSON authority, unknown-not-zero semantics, field provenance, America/New_York day assignment, Apple Health canonical steps, tombstones/revisions, and no local-runtime dependency for ChatGPT execution
- Live personal-artifact migration was performed separately and is intentionally not represented with private record counts in this public report.

## Implemented slices

1. Product identity/versioning: GTIN/UPC normalization, deterministic formulation fingerprints, ambiguity and reformulation states.
2. Multidimensional confidence: identity, portion, and composition dimensions separate from nutrient tiers.
3. Nutrient coverage: item-, calorie-, and confidence-weighted coverage with adequacy gating.
4. Deterministic resolution: explicit source ladder and unresolved/ambiguous results.
5. Barcode fast path: fresh local reuse, stale revalidation, and offline-safe outcomes.
6. Reported versus enriched nutrients: per-field reported/analytical/selected values and reasons.
7. Integrity review queue: numeric, macro, sugar/fat, and quantity invariants with severity.
8. Food-master debt: usage, calorie contribution, unknown nutrients, and staleness prioritization.
9. Longitudinal summaries: mean, median, range, target-hit frequency, and coverage-aware interpretation.
10. Nutrient contributions: deterministic source aggregation excluding unknowns and tombstones.
11. Nutrition/activity joins: training/rest comparisons and future-leakage-safe pre-workout windows.
17. Migration: repeatable non-destructive v2 fixture migration preserving IDs, values, revisions, and tombstones.

## Data quality and safety

- No canonical personal data was modified or embedded in fixtures.
- No credentials, tokens, or private history were added.
- Historical entries remain independent of later food-master or enrichment changes.
- External-source failure behavior remains explicit; fresh verification is never invented.

## Test results

- Final regression suite: **124 passed, 0 failed, 0 skipped**
- Public plugin validator: passed
- `git diff --check`: passed

## Remaining integration work

The public repository now contains tested primitives for the remaining operational
features, but the private Library-backed workbook projection and personal ledger
migration must be exercised against the user's actual Library artifacts before
those artifacts can be declared migrated. That step is intentionally not faked
inside a public repository.
