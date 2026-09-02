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
- If canonical entries and current state disagree, canonical active entries win; include the canonical item in the report and mark/rebuild the state as stale.
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

## Offline reference CLI shortcuts

When operating in a Codex/developer environment with local ledger artifacts, use the streamlined reference CLI paths below instead of rediscovering schemas from tests or dumping raw masters:

- Import archive setup: `nutrition_tracker.py --ledger Fitness_Ledger_Nutrition_Ledger.json setup-import --source-dir <package-dir>`. This promotes `IMPORT_Nutrition_Ledger.json` and `IMPORT_Nutrition_Current_State.json` to the canonical working filenames. Use `--force` only when the user explicitly wants to replace existing working copies.
- Read-only reports: `--state` is optional for `day`, `daily-totals`, `weekly-totals`, `panel`, `foods`, and `validate`; the script derives the sibling current-state filename from `--ledger`.
- Standard report commands: use `daily-totals --date <YYYY-MM-DD>`, `weekly-totals --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD>`, `foods --date <YYYY-MM-DD>`, and `panel --date <YYYY-MM-DD>`. Do not hand-format a different layout.
- Target updates: use `targets --daily-calories <kcal>`, `--daily-protein-g <g>`, `--daily-carbohydrates-g <g>`, `--daily-fat-g <g>`, and/or `--daily-fiber-g <g>` to persist personal daily targets after setup.
- Raw entry schema: run `entry-template --meal <meal> --food-product <name>` to get the supported JSON payload for `add --fields`.
- Food-master matching: run `food-master-find --query "<terms>" --summary` first. Use the full output only when provenance details are needed.
- Portion scaling: prefer `add-from-master --amount-grams <g>` when the selected master has `serving_weight_g`; prefer `--servings <n>` for serving counts. Use `--factor` only when neither human-scale option fits.
- Explicit dates for mutations still require `--date-source user_explicit`, even when the requested date is today.

If these shortcuts do not cover a natural logging request, treat that as a skillset gap and add a tested CLI affordance rather than relying on ad hoc JSON construction.

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

## Absolute nutrition-output invariant

This section governs every human-readable nutrition response, including food
adds, multi-food adds, recipe adds, corrections, deletions, hydration logs,
weight logs, target changes, daily reports, weekly reports, and panels. It has
priority over any instruction to be concise.

- Nutrition responses are typed Markdown documents generated from the
  canonical output contract, never free-form conversational summaries.
- Prose, bullets, sentence-form totals, alternate layouts, abbreviated tables,
  paraphrased tables, and selected-nutrient summaries are prohibited for
  nutrition data.
- Every food mutation MUST contain a `Logged Food` or `Logged Foods` Markdown
  table followed by a `Today So Far` Markdown table. The item table MUST use
  the approved columns, including `Water Added`; the totals table MUST use the
  approved metric rows and target column.
- Every response MUST include the required status, target-progress, and
  persistence/read-back information in the approved locations. Include a
  `Data quality` section whenever an item is estimated, held, ambiguous,
  partially completed, or has unknown values. `Sources` MUST be last whenever
  source links exist.
- A partial mutation MUST be reported structurally: logged items belong in the
  logged-items table, and unlogged or held items belong in a clearly labeled
  structured data-quality section. Do not hide partial completion in prose.
- Unknown values MUST be table cells containing `unknown`; never omit a column,
  row, nutrient, item, or status because its value is unavailable.
- Before sending, validate the rendered response for required headings, section
  order, table headers, column counts, row presence, units, unknown handling,
  and source placement. If validation fails, fail closed: do not substitute
  prose; repair and re-render, or report a formatting failure.
- Do not manually compose a nutrition response when the canonical renderer or
  approved example contract is available. Relay canonical renderer output
  verbatim for reports.

All human-readable nutrition reports use one stable Markdown table contract. No conversational response should vary the style, section names, column order, units, or handling of unknowns unless the user explicitly asks for raw JSON or a one-off export format. For `panel`, `foods`, `daily-totals`, and `weekly-totals`, relay the renderer output verbatim and in full. This is a hard output invariant: never collapse any report into prose, a code-block summary, partial highlights, selected nutrients, or "key foods"; never paraphrase or truncate the tables. Only produce a summary when the user explicitly asks for a summary instead of the report.

Canonical report grammar:

1. Header line: `<Report Name> | <YYYY-MM-DD or range> | <IANA timezone>`.
2. Blank line.
3. `Daily Totals`, `Weekly Totals`, or `Daily Rows` section label as applicable.
4. Markdown tables only; no bullet lists for foods, macros, micros, daily totals, weekly totals, or panels.
5. Final `Data quality` section with `Active entries only. Unknown means untracked, not zero.`

Use these exact table shapes:

```text
Daily Totals
| Metric | Amount | Target |
| --- | --- | --- |
| Entries | <count> | active foods only |
| Weight | <lb or not logged> | body weight |
| Calories | <amount> | <target progress or not set> |
| Protein | <amount> | <target progress or not set> |
| Carbs | <amount> | <target progress or not set> |
| Fat | <amount> | <target progress or not set> |
| Fiber | <amount> | <target progress or not set> |
| Hydration | <mL and fl oz or unknown> | drinks + food water |

Foods
| Meal | Food | Amount | Calories | Protein | Carbs | Fat | Fiber | Water Added |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Micronutrients
| Nutrient | Amount | DRV % |
| --- | --- | --- |
```

Weekly totals add this exact leading table before the weekly totals and micronutrient tables:

```text
Daily Rows
| Date | Entries | Calories | Protein | Carbs | Fat | Fiber | Hydration |
| --- | --- | --- | --- | --- | --- | --- | --- |
```

`panel`, `foods`, `daily-totals`, and `weekly-totals` must share this contract: fixed header grammar, fixed table names, fixed column order, fixed meal order, explicit unknowns, and no internal protein-credit field. `panel` means full macros plus all tracked micronutrients.

Natural-language routing:

- `Show today's food`, `what did I eat today`, and equivalents → `foods`.
- `Today's panel`, `today's numbers`, and equivalents → `panel`.
- `Full nutrient panel` → `panel`.
- `Daily totals` → `daily-totals`.
- `Weekly totals` → `weekly-totals`.

Before either report, resolve canonical history first and select active entries for the configured local date. If `Current_State` disagrees, canonical history wins and the cache is stale.

For `foods`, show `Daily Totals` and the `Foods` table only.

For `panel`, show `Daily Totals`, `Foods`, and `Micronutrients`. The `Target` column uses personal calorie/protein/carbs/fat/fiber targets when configured. The micronutrient `DRV %` column uses `targets.daily_nutrient_targets` as the denominator when configured. The column renders as `not set` when no reference target exists for that nutrient (even if the amount is also unknown), and as `unknown` only when a reference target is configured but the amount has not been tracked. Missing values are never converted to zero.

For micronutrients, show every tracked nutrient amount, DRV context, and `unknown` for missing fields. Do not omit a micronutrient just because it is unknown.

Vitamin labels must include both the standard letter/number designation and the common name, such as `Vitamin B1 (Thiamin)`, `Vitamin B2 (Riboflavin)`, `Vitamin B3 (Niacin)`, `Vitamin B5 (Pantothenic acid)`, `Vitamin B6`, `Vitamin B7 (Biotin)`, `Vitamin B9 (Folate)`, and `Vitamin B12 (Cobalamin)`.

## Output after a successful mutation

Use the absolute nutrition-output invariant above for every mutation. A food,
recipe, hydration, weight, correction, deletion, or target mutation MUST use
the applicable approved Markdown table contract; “concise” means omit unrelated
detail, not that tables may be replaced with prose. Include explicit
persistence/read-back confirmation, including the verified ledger revision when
available. Material estimates, assumptions, or unresolved identity issues
belong only in the structured `Data quality` section.

When a mutation uses an external product page, food database, or other web reference, append a `Sources` section after `Data quality` with compact Markdown links to the sources used for the logged item. Keep source links at the bottom of the response and distinguish product-label sources from estimates when relevant. Do not invent URLs. If a source has no retrievable link, it cannot be used as sourced provenance.

### Mandatory source-link gate

Every nutrient value obtained from an external source must have a retrievable Markdown link recorded in the entry provenance and shown in the response's `Sources` section. This applies to every source type, including USDA, manufacturer labels, retailer pages, and third-party databases. A USDA claim requires a direct USDA/FoodData Central link; do not label remembered, inferred, or generic values as USDA-derived without that link. Never use memory, educated guessing, or an unlinked "USDA-style" profile to fill nutrient values. If a suitable linked source cannot be found, do not silently estimate or log the item as verified: ask for a package label/product link or explicitly log it only as an unverified estimate after the user agrees.

Every food master/catalogue record must include a direct `source_url` (or an equivalent direct URL in its source metadata) for the nutrient profile. When a recipe is reused, cite the local recipe/catalogue record in the response rather than repeating every ingredient link, but retain the ingredient-level source URLs in the saved records. Before using an existing record, check that its source URL is present and retrievable; records without one are not eligible for silent reuse and must be backfilled or held for source verification.

Recipe and composite food masters may have multiple sources. Store them as a `source_urls` array of direct URLs, one per ingredient/source, rather than as an opaque prose string. Accept legacy comma-separated source values only as an input format and normalize them to the array before reuse. A reused recipe response may cite the local catalogue record, but the catalogue record must retain all ingredient-level links. Backfill the catalogue source by source; never invent, infer, or silently preserve an unlinked source claim.

## Safety boundary

This is a data-quality and tracking workflow, not medical diagnosis or treatment. Do not infer deficiencies from one day or incomplete coverage. Keep the user in control of mutations and do not transmit ledger contents to external services unless explicitly requested.

Read [the schema reference](references/schema.md) before modifying schema, provenance, cache, or workbook behavior.

For the canonical food-add response examples, read [references/add-output-examples.md](references/add-output-examples.md). Follow their section order, headings, and placement rules when formatting single-food, multi-food, estimate, data-quality, source, and ordering cases, while treating numeric values and any real links as illustrative rather than mandatory and never inventing source links.

The offline reference modules in `scripts/` expose identity/versioning, confidence, coverage, source resolution, barcode, enrichment, invariants, debt, longitudinal, contribution, activity-join, migration, and Library-revision primitives. They are testable building blocks; runtime persistence must still follow the Library contract above.
