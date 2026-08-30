# Release checklist

## Scope and privacy

- [ ] Bundle contains skills only: no MCP server, hosted service, account connection, telemetry, or secret.
- [ ] Repository contains no real ledger, health export, food photo, API key, user identifier, absolute local path, or private file reference.
- [ ] `PRIVACY.md`, `SECURITY.md`, and `CONTRIBUTING.md` are current.
- [x] MIT License is included; retain its copyright, permission, and warranty notices in substantial copies.

## Reliability

- [ ] Run `python3 -m unittest discover -v tests` from the repository root.
- [ ] Run the eight cases in `PLUGIN_TEST_MATRIX.md` on a fresh sample ledger.
- [ ] Validate the manifest using the Codex plugin validator available in the release environment.
- [ ] Confirm the skills use the configured timezone, preserve corrections and source snapshots, and never replace unknown nutrition data with zero.

## Packaging

- [ ] Increment the semantic version in `.codex-plugin/plugin.json`.
- [ ] Update `CHANGELOG.md`.
- [ ] Review `git status --ignored` for accidental private data.
- [ ] Test installation from a clean clone before publishing or submitting the plugin.
