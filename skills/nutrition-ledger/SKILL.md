---
name: nutrition-ledger
description: Log food, hydration, and body weight into an auditable ChatGPT Library nutrition ledger; use for corrections, daily panels, and provenance-aware nutrient totals.
---

# Nutrition Ledger

Use this skill for logging, correcting, inspecting, or summarizing nutrition data. Keep the conversation natural, but persist successful mutations to the user's ChatGPT Library. Never substitute conversational memory or a stale cache for canonical history. The runtime must never require a local filesystem path, a local process, or manual spreadsheet maintenance for ordinary ChatGPT logging.

## Library-native persistence

- Search Library for the user's selected logical ledger before every report or mutation.
- **Canon-first is mandatory:** resolve and read the canonical ledger before reading `Fitness_Ledger_Nutrition_Current_State.json`.
- Read candidate canonical ledger contents before using `Current_State`; search snippets alone are not authoritative. `Current_State` is never the primary read source.
- If canonical entries and current state disagree, canonical active entries win. Include the canonical item in the report and mark/rebuild the state as stale.
- Never answer “show today’s foods” or equivalent from current state alone.
- A skills-only plugin does not itself provide an in-place Library replacement action. Do **not** claim that such an action exists merely because this skill describes persistence.
- Portable ChatGPT persistence uses a **revisioned successor artifact**: validate the proposed full JSON ledger, stamp the next `_fitness_ledger_revision`, create that complete file through the runtime's file-generation capability so ChatGPT saves it to Library, then read/search Library again and verify the revision/fingerprint before claiming success.
- Legacy/import ledgers without `_fitness_ledger_revision` are revision `0`. Existing names such as `IMPORT_Nutrition_Ledger.json` remain valid canonical roots.
- When several ledger artifacts exist, select the unique highest valid revision by content metadata, never by filename order or timestamp alone. Different artifacts claiming the same latest revision are a blocking conflict.
- If the active runtime actually exposes a guarded Library replace/write action, it may be used instead, but only after the capability is observed and the successful write is verified by canonical read-back.
- Never ask a mobile user to run a local command or manually maintain a spreadsheet just to log food.

Read [the Library persistence contract](references/library-contract.md) before implementing or changing read, mutation, cache, or conflict behavior. `scripts/library_revision.py` is the offline developer/test reference implementation for revision fingerprinting and canonical selection.

## Core rules

- The JSON ledger is canonical history; daily state is rebuildable cache; workbooks are reporting projections.
- Preserve corrections and deletions in the audit log. Do not silently overwrite history.
- Track nutrient provenance per field: A label/direct, B authoritative reference, C reconstructed estimate, D unknown.
- Track identity, portion, and composition confidence separately.
- Missing means `unknown`, not zero. Preserve source-declared zeroes.
- Prefer package labels for branded foods. Use authoritative generic references for ordinary unbranded staples when appropriate.
- Scale known nutrients for weighed portions.
- Report item-, calorie-, and confidence-weighted nutrient coverage and avoid adequacy claims when coverage is insufficient.
- Validate before persistence and reconcile from canonical history before reporting.

## DATE PREFLIGHT — REQUIRED BEFORE EVERY DATE-SENSITIVE OPERATION

Before any daily report, food log, hydration log, weight log, correction, deletion, fitness sync, or other date-sensitive operation:

1. Read the canonical ledger or initialization settings and resolve the configured IANA timezone.
2. If the timezone is missing or invalid, stop and ask the user to configure it. A detected timezone is a setup suggestion only and requires explicit user confirmation and persistence before proceeding.
3. Compute the current local date from the configured timezone and current instant. Never use the host/runtime date, UTC calendar date, or an unqualified local host date.
4. Show the resolved timezone and local date before mutation, for example: `Target ledger date: 2026-09-01 (America/New_York).`
5. Preserve explicit historical dates as user-assigned dates.
6. Store the timezone used for new entries when schema supports it.
7. Treat failed preflight as blocking.

A successful mutation still requires canonical read-back verification. If persistence or read-back verification cannot be completed, say `not persisted` and do not claim success.

## Mutation transaction

For food, hydration, weight, target, correction, deletion, or food-master mutations:

1. Resolve canonical ledger and its revision/fingerprint.
2. Resolve identity, amount, nutrients, provenance, meal, date, and any material assumptions.
3. Apply the mutation in memory.
4. Validate schema, invariants, dates, quantities, nutrient values, provenance, idempotency, audit history, and cache consistency.
5. Rebuild current state from the proposed canonical ledger.
6. Stamp the proposed full ledger as the next revision using the immediately previous canonical fingerprint.
7. Materialize the complete successor ledger as a ChatGPT-created JSON file so it is saved to Library. Preserve the logical canonical filename when possible; otherwise use a deterministic revision suffix.
8. Search/read Library again and verify that the successor revision and fingerprint match exactly.
9. Only after step 8 succeeds may derived current state be materialized and the user be told the mutation persisted.
10. If a competing successor, conflict, failed file creation, or failed read-back occurs, fail closed and report `not persisted`.

Do not treat a sandbox/local temporary file as durable persistence evidence. The verification target is the Library artifact.

## Product identity and versioning

Food masters may carry GTIN/UPC, brand/manufacturer, product name, variant, package and serving attributes, source identifiers, verification timestamps, and a deterministic formulation fingerprint. A same-GTIN formulation change creates a new version linked by `supersedes_food_master_id`; it never rewrites historical entries. Name-only matches remain ambiguous and must not receive unjustified Tier-A identity confidence.

## First-run setup

For a new user, initialize a ledger before logging data. Require a confirmed IANA timezone and collect only goals the user chooses to set. Optional Apple Health and Caliber selections record source-adapter intent, not credentials or a claimed live connection.

Initialization may store a preferred daily combined synchronization time. Do not claim an external scheduled task exists unless the host explicitly confirms that capability.

## Daily reports

`panel` and `foods` share one stable report contract: header, active entry count, fixed meal order, individual food lines, meal subtotals, daily totals, hydration, targets, and explicit unknowns. Use plain protein totals; do not expose internal protein-credit fields.

Natural-language routing:

- `Show today's food`, `what did I eat today`, and equivalents → `foods`.
- `Today's panel`, `today's numbers`, and equivalents → `panel`.
- `Full nutrient panel` → `panel` plus the micronutrient section.

Before either report, resolve canonical history first and select active entries for the configured local date. If `Current_State` disagrees, canonical history wins and the cache is stale.

For `foods`, show every active entry grouped by fixed meal order, then meal subtotals and full-day totals.

For `panel`, include the same individual entries and totals plus progress and micronutrients. The Progress section uses personal calorie/protein/fiber targets when configured; `%DV` belongs in the micronutrient section, not personal-target progress.

For micronutrients, show amount plus %DV/reference for known values and `unknown` for missing fields.

## Conversational output after a successful log

Show:

1. Ledger date and configured timezone.
2. Every newly added item with amount, calories, protein, carbohydrates, fat, and fiber; use `unknown` when unavailable.
3. A subtotal for each affected meal/snack group.
4. Updated daily totals for calories, protein, carbohydrates, fat, fiber, and tracked drinking water.
5. Remaining/overage versus configured calorie, protein, and fiber targets when available.
6. Material estimates, assumptions, or unresolved identity issues.
7. Explicit persistence/read-back confirmation including the verified ledger revision when available.

A summary-only response is allowed only when the user explicitly asks for one.

## Safety boundary

This is a data-quality and tracking workflow, not medical diagnosis or treatment. Do not infer deficiencies from one day or incomplete coverage. Keep the user in control of mutations and do not transmit ledger contents to external services unless explicitly requested.

Read [the schema reference](references/schema.md) before modifying schema, provenance, cache, or workbook behavior.

The offline reference modules in `scripts/` expose identity/versioning, confidence, coverage, source resolution, barcode, enrichment, invariants, debt, longitudinal, contribution, activity-join, migration, and Library-revision primitives. They are testable building blocks; runtime persistence must still follow the Library contract above.
