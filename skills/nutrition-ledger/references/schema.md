# Nutrition ledger schema

The ledger is a JSON object with `entries`, `weights`, `food_master`, `audit_log`, `targets`, `timezone`, `source_adapters`, and `sync`. `timezone` is required and must be an IANA identifier such as `Europe/London`; it defines every daily boundary and must not be inferred from the runtime environment. `source_adapters` records user-configured integration intent and status only; it must never contain credentials, account exports, or a claim that a live connection succeeded without a separate connector check.

- Active entries have `deleted_at: null`; tombstoned entries remain in history.
- Each entry needs a stable `entry_id`, `date`, `food_product`, `revision`, and nutrient fields as available.
- Per-field provenance belongs in `nutrient_provenance.<nutrient>` and uses A/B/C/D confidence tiers.
- `daily_cache` and the separate state file are derived views, tied to active ledger entries by `ledger_fingerprint`.
- A food-master record is reusable only when product identity, brand, flavor/formulation, and serving basis agree.
