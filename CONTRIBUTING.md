# Contributing

Use test-driven development for behavior changes: add or update a failing regression test, implement the smallest change, then run the full suite.

Preserve these invariants: local-first data ownership, explicit provenance, unknown is not zero, immutable audit history, idempotent reconciliation, and no cross-source activity summing.

Contributions must not add real personal health data, secret material, or undocumented network calls.

Every pull request must include a semantic version bump in `.codex-plugin/plugin.json`, `pyproject.toml`, and `CHANGELOG.md`. Use:

```bash
python3 scripts/release_workflow.py bump patch --message "Describe the user-visible change."
```

Use `minor` for new user-visible workflows or capabilities and `major` for breaking changes.

After the PR merges, create the matching release tag from `main`:

```bash
python3 scripts/release_workflow.py tag-release --push
```

The tag must be `vX.Y.Z` for the checked-out plugin version. The release workflow validates the tag and creates the GitHub Release.
