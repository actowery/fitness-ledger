## Summary

Describe the user-visible behavior and the reason for the change.

## Verification

- [ ] I added or updated a failing test before implementation when behavior changed.
- [ ] I bumped `.codex-plugin/plugin.json`, `pyproject.toml`, and `CHANGELOG.md` using semantic versioning.
- [ ] `python3 -m unittest discover -v -s tests` passes locally.
- [ ] This change adds no personal health data, secrets, or undocumented network access.
- [ ] I called out any change to workflows, release behavior, or plugin permissions.

## Release after merge

- [ ] Create and push the matching `vX.Y.Z` tag.
- [ ] Confirm the release workflow created the GitHub Release.

## Security considerations

Describe security-relevant effects, or write `None`.
