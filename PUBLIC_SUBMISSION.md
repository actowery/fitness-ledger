# Public plugin submission packet

This packet prepares Fitness Ledger 0.2.1 for a **Skills only** submission to the universal ChatGPT and Codex Plugins Directory.

## Listing

| Field | Submission value |
| --- | --- |
| Package name | `fitness-ledger` |
| Version | `0.2.1` |
| Display name | Fitness Ledger |
| Short description | Track nutrition and fitness |
| Developer name | Fitness Ledger Contributors; use the verified individual or business identity selected in the OpenAI Platform if review requires an exact publisher-name match |
| Category | Healthcare |
| Website | https://github.com/actowery/fitness-ledger |
| Support | https://github.com/actowery/fitness-ledger/issues |
| Privacy policy | https://github.com/actowery/fitness-ledger/blob/main/PRIVACY.md |
| Terms | https://github.com/actowery/fitness-ledger/blob/main/TERMS.md |

### Long description

Maintain a provenance-aware nutrition and fitness ledger in ChatGPT Library. Log food, hydration, and weight; correct entries without losing history; generate deterministic daily reports; and reconcile workout and activity snapshots without silently combining conflicting sources. Missing nutrient values remain unknown rather than becoming fabricated zeroes.

Fitness Ledger is skills-only: it has no publisher-hosted service, telemetry, or required external account. Optional source connections remain separate and user controlled. It supports personal tracking and explanation, not medical diagnosis or treatment.

### Starter prompts

1. Set up my Fitness Ledger in ChatGPT Library.
2. Log what I ate today and show my nutrition report.
3. Reconcile my latest workout and step-count snapshots.

## Reviewer test cases

Use a fresh copy of `examples/sample_ledger.json` and the synthetic facts below. Do not use a real person's health data.

### Positive cases

| ID | Prompt | Fixture or prerequisite | Expected behavior | Expected result shape |
| --- | --- | --- | --- | --- |
| P1 | Set up my Fitness Ledger for `America/New_York`. | No existing canonical files. | Create or resolve the canonical Library ledger and state, preserve the explicit timezone, and leave personal targets unset unless supplied. | A setup confirmation naming the timezone and canonical files; a valid ledger with `targets: {}`. |
| P2 | Log breakfast today: 250 mL labelled protein drink, 160 calories, 30 g protein, 4 g carbohydrate, and 2.5 g fat. | P1 completed. | Append one breakfast entry using label provenance and the ledger-local date. Do not infer unlisted micronutrients as zero. | One new entry plus a daily report containing Nutrition Panel and Foods Eaten sections. |
| P3 | Log 150 g of a food whose label values are per 100 g: 200 calories, 10 g protein, 20 g carbohydrate, and 8 g fat. | P1 completed. | Scale the consumed nutrients by 1.5 while preserving the original per-100-g source facts. | One entry with 300 calories, 15 g protein, 30 g carbohydrate, and 12 g fat plus unchanged source facts. |
| P4 | Correct the protein drink from P2 to 170 calories; keep everything else the same. | P2 completed and its entry ID available. | Create a correction linked to the original entry, preserve the before snapshot, and count only the corrected value in current totals. | An auditable correction record and a report showing 170 rather than 160 calories for that item. |
| P5 | Reconcile these snapshots for today: Apple Health steps 9,250 recorded at 20:00; Caliber steps 6,400 recorded at 18:00; one Caliber workout with stable ID `workout-demo-1`. | P1 completed; source policy gives Apple Health canonical step precedence. | Preserve both raw observations, select 9,250 canonical steps without addition, and retain the workout by stable ID. | Raw source snapshots, one canonical step total of 9,250, and one normalized workout. |

### Negative cases

| ID | Prompt or scenario | Expected safe behavior | Why it must not proceed |
| --- | --- | --- | --- |
| N1 | At 00:05 near a date boundary, say only “log this for yesterday” when the ledger timezone is missing. | Ask for the user's IANA timezone and make no mutation. | Guessing could silently assign the entry to the wrong date. |
| N2 | Log a food with `-100` calories or a negative quantity. | Reject the invalid values with a clear validation error and make no partial write. | Nutrition quantities cannot be negative and a partial mutation would corrupt totals. |
| N3 | Combine Apple Health 9,250 steps and Caliber 6,400 steps even though no source-precedence policy is configured. | Preserve both observations, flag the conflict, and decline to publish or sum a canonical total. | Adding competing observations double-counts the same activity. |

## Initial release notes

Initial public submission of Fitness Ledger 0.2.1, a Library-native, skills-only plugin for provenance-aware nutrition logging, deterministic reports, auditable corrections, and fitness-source reconciliation. This release contains no hosted service, MCP server, telemetry, or bundled authentication. It uses generic `Fitness_Ledger_*` filenames, treats missing nutrients as unknown rather than zero, preserves source observations, and prohibits medical diagnosis or treatment.

## Submission checklist

- [ ] Select an OpenAI Platform organization where the submitter is an owner or has Apps Management write access.
- [ ] Complete individual or business identity verification and choose the matching verified identity.
- [ ] Create a **Skills only** draft in the plugin submission portal.
- [ ] Upload the final plugin/skills bundle from the reviewed commit.
- [ ] Copy the listing, prompts, tests, availability, and release notes from this packet.
- [ ] Select only countries where the publisher is ready to support the plugin.
- [ ] Complete policy attestations after automated skill scans pass.
- [ ] Submit for review; after approval, explicitly publish the approved version.
