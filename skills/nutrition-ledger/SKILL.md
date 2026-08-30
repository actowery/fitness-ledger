---
name: nutrition-ledger
description: Log food, hydration, and body weight into a local, auditable nutrition ledger; use for corrections, daily panels, and provenance-aware nutrient totals.
---

# Nutrition Ledger

Use this skill when the user wants to log, correct, inspect, or summarize their nutrition data. Keep the conversation natural, but store entries in a local JSON ledger supplied or created by the user. Do not assume a cloud account, a specific filename, or a private data store.

## Core rules

- Treat the JSON ledger as canonical; a daily state file is rebuildable cache.
- Require a persisted IANA timezone (for example, `Europe/London`) before assigning dates. Offer a detected local timezone only as a setup suggestion; never infer it from the runtime clock or silently default to a region.
- Preserve corrections and deletions in the audit log. Do not silently overwrite history.
- Track nutrient provenance per field: A label/direct, B authoritative reference, C reconstructed estimate, D unknown.
- Missing is `unknown`, not zero. Retain source-declared zeroes.
- Use package labels before generic databases for branded food. Scale known nutrients for weighed portions.
- Before reporting, reconcile from the ledger and validate it. Never report from a stale cache alone.

## First-run setup

For a new user, initialize a ledger before logging data. Require a confirmed IANA timezone; collect only the goals the user chooses to set. Optional Apple Health and Caliber selections record local adapter intent, not credentials or a claimed live connection.

Initialization also configures the daily combined synchronization schedule. Default it to `23:55` in the user's configured local timezone (near midnight), and ask for a different `HH:MM` time if desired. The schedule must be stored in the ledger; never interpret it in UTC or the runtime host timezone. The scheduled run checks nutrition, Caliber workouts, Apple Health workouts, and Apple Health activity every day, including rest days. A successful run records its completion; a failed or incomplete source check must be reported and must not publish derived fitness facts.

```bash
python3 scripts/nutrition_tracker.py --ledger <ledger.json> --state <state.json> init \
  --timezone Europe/London --daily-calories 2000 --daily-protein-g 150 \
  --source apple-health --source caliber --sync-time 23:55
```

Do not overwrite a ledger during onboarding. `--force` is reserved for an explicit replacement request.

## Daily reports

Run the bundled script for deterministic operations:

```bash
python3 scripts/nutrition_tracker.py --ledger <ledger.json> --state <state.json> panel --date YYYY-MM-DD
```

`panel` and `foods` have one stable report contract: header, active entry count, fixed meal order, consistent food lines, hydration, and explicit unknowns. Use plain protein totals; do not expose internal protein-credit fields.

For micronutrient panels, append a clearly labeled nutrient section after the canonical daily panel. Show amount plus %DV/reference for each known nutrient and `unknown` for missing fields.

## Safety boundary

This is a data-quality and tracking workflow, not medical diagnosis or treatment. Do not infer nutrient deficiencies from one day or incomplete coverage. Keep the user in control of every mutation and do not transmit ledger contents to external services unless they explicitly ask for it.

Read [the schema reference](references/schema.md) before modifying schema, provenance, cache, or workbook behavior.
