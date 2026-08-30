# Fitness Ledger

Fitness Ledger is a local-first skill bundle for conversational nutrition logging, deterministic daily reporting, and fitness-source reconciliation. It is designed for people who want AI convenience without opaque, silently changing health records.

## What it includes

- `nutrition-ledger`: provenance-aware food, hydration, and weight logging with corrections, tombstones, validation, and consistent reports.
- `fitness-sync`: pure validation and reconciliation helpers for workout/activity snapshots.

No account, hosted service, telemetry, or bundled health-data connection is required. Users own their ledger files and choose any optional source adapters separately.

Each ledger must declare its own IANA timezone (for example, `Europe/London`). Date assignment uses that saved setting, never the host machine's clock or a regional default.

## Install and test locally

Install the plugin from a local marketplace or open the folder in Codex. Then run:

```bash
python3 -m unittest discover -v tests
```

Validate the manifest with the plugin validator provided by your Codex development environment before packaging a release.

Start with `examples/sample_ledger.json`; do not commit real food logs, health records, photos, API keys, or connected-account exports.

## Scope

This plugin tracks and explains data. It does not provide medical diagnosis, treatment, or a hosted health service.

## License

[MIT](LICENSE): people may use, modify, redistribute, sublicense, or sell copies, provided the copyright and permission notice travel with substantial copies. It is provided without warranty.
