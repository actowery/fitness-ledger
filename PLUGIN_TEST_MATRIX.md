# Plugin test matrix

Run these cases against a fresh copy of `examples/sample_ledger.json`. Record the plugin version, the prompt, the observed result, and whether any ledger mutation occurred.

## Positive cases

| ID | Scenario | Expected result |
| --- | --- | --- |
| P1 | Log a labelled breakfast for today. | One append-only nutrition entry with label provenance; the daily panel uses the configured timezone. |
| P2 | Log a 150 g portion from a 100 g label. | Calories and nutrients scale by 1.5; source label values remain unmodified. |
| P3 | Correct a prior entry. | The correction references the original entry, preserves audit history, and the report reflects only the corrected value. |
| P4 | Reconcile a fitness sync containing a workout and a later step-count update. | The source snapshots are preserved and the canonical result follows the configured source policy without adding competing step counts. |
| P5 | Sync a rest day with no workouts. | The run succeeds, records the checked interval, and does not invent a workout or delete earlier history. |

## Negative cases

| ID | Scenario | Expected safe behavior |
| --- | --- | --- |
| N1 | Request a log with an ambiguous date near midnight. | Ask for or apply the configured project timezone; do not silently place it on a different day. |
| N2 | Supply a negative nutrient value or a malformed food payload. | Reject the payload with a clear validation error and make no partial write. |
| N3 | Supply conflicting automatic activity sources with no configured precedence. | Preserve both observations, flag the conflict, and decline to publish a canonical total. |

## Acceptance rule

All eight cases must pass on the release candidate. Any silent date shift, dropped correction history, fabricated zero, or source-total addition blocks release.
