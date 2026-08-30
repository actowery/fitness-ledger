---
name: nutrition-ledger
description: Log food, hydration, and body weight into an auditable ChatGPT Library nutrition ledger; use for corrections, daily panels, and provenance-aware nutrient totals.
---

# Nutrition Ledger

Use this skill when the user wants to log, correct, inspect, or summarize their nutrition data. Keep the conversation natural, but store entries in the user's persistent ChatGPT Library files. The canonical ledger is a Library file; never require a local filesystem path, a local process, or manual spreadsheet maintenance.

## Library-native persistence

- Search Library by the canonical filenames or the user's selected Library reference before reading or mutating data.
- Use the existing Library identity and current version when reading. Never create a duplicate copy when the canonical file already exists.
- Read the canonical ledger before every report or mutation; do not rely on search snippets or a cached state file alone.
- For a mutation, preserve the ledger's Library identity and replace that same Library file only after validation and state reconciliation succeed.
- Treat `Fitness_Ledger_Nutrition_Ledger.json` as canonical history and `Fitness_Ledger_Nutrition_Current_State.json` as rebuildable cache. The workbook is a reporting projection, not the operational source of truth.
- If a required Library file cannot be resolved, ask the user to select or upload it. Do not silently create an unrelated local ledger.

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

After initialization succeeds, store the requested sync configuration in the Library ledger. Do not claim that an external scheduled task exists unless the host explicitly provides and confirms that capability. A user-controlled daily automation may be offered, but its absence must not block ordinary mobile logging and reporting.

Do not overwrite a ledger during onboarding. `--force` is reserved for an explicit replacement request.

## Daily reports

The bundled script is an offline developer/test reference. The ChatGPT runtime must use Library reads and replacements for persistence; mobile users must not be asked to run a command or depend on a local script.

Use the canonical renderer contract encoded in the ledger and skill. When the offline reference implementation is available in a development environment, it may be used for validation.

`panel` and `foods` have one stable report contract: header, active entry count, fixed meal order, consistent food lines, hydration, and explicit unknowns. Use plain protein totals; do not expose internal protein-credit fields.

Natural-language report routing is mandatory:

- “Show today’s food,” “what did I eat today,” or equivalent requests map to `foods`.
- “Today’s panel,” “today’s numbers,” or equivalent requests map to `panel`.
- “Full nutrient panel” maps to `panel` followed by the labeled micronutrient section.
- Never manually reconstruct a daily report from raw JSON, a cache, or ad-hoc calculations when the canonical renderer is available.
- The Progress section reports calories and protein against the user’s personal targets (when configured), never FDA Daily Values. `%DV`/reference percentages belong only in the micronutrient section.
- If a personal target is unavailable, render the target as unavailable; do not substitute a generic DV.

For micronutrient panels, append a clearly labeled nutrient section after the canonical daily panel. Show amount plus %DV/reference for each known nutrient and `unknown` for missing fields.

## Safety boundary

This is a data-quality and tracking workflow, not medical diagnosis or treatment. Do not infer nutrient deficiencies from one day or incomplete coverage. Keep the user in control of every mutation and do not transmit ledger contents to external services unless they explicitly ask for it.

Read [the schema reference](references/schema.md) before modifying schema, provenance, cache, or workbook behavior.

Read [the Library persistence contract](references/library-contract.md) before implementing or changing Library-backed read, mutation, cache, or conflict behavior.
