# Library persistence contract

This plugin uses ChatGPT Library as its persistence boundary. The conversation is the interface; Library files are the durable record.

## Canonical files

- `Battle_Mage_Nutrition_Ledger.json` is the canonical nutrition history, food master, provenance, targets, and audit log.
- `Battle_Mage_Nutrition_Current_State.json` is a rebuildable current-day cache and must never be treated as authoritative by itself.
- `Battle_Mage_Nutrition_Weight_Tracker.xlsx` is a reporting projection. It is not the operational source of truth.
- Fitness synchronization may use a separate canonical fitness/join file established during setup. Do not invent a filename when an existing Library reference is available.

## Read path

1. Resolve the selected Library reference or search Library for the canonical filename.
2. Read the current canonical ledger and its current version before every report or mutation.
3. If the ledger is large, use the Library-supported materialization/edit path; do not ask the mobile user to download or run anything.
4. Reconcile current state from canonical entries before displaying totals.

## Mutation path

1. Resolve identity and nutrient provenance without changing the ledger.
2. Apply the append, correction, tombstone, or food-master mutation in memory.
3. Validate schema, dates, quantities, nutrient values, provenance, idempotency, and cache consistency.
4. Rebuild the current-state cache from the proposed canonical ledger.
5. Replace the same Library file identity using its retained current-version guard.
6. If the guarded replacement conflicts, reread the latest file, reapply the user mutation, and validate again. Never overwrite a newer version blindly.
7. Update the state file only after the canonical ledger replacement succeeds.

No partial mutation is successful. If any validation or write fails, report that the ledger was not changed.

## Reporting path

Reports use active canonical entries only, fixed meal ordering, explicit unknowns, and the configured IANA timezone. Missing nutrients remain unknown rather than zero. A report may be produced without updating the workbook; workbook synchronization is a separate projection step.
