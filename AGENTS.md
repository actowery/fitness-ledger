# Fitness Ledger Agent Workflow

This repository is a live personal tracking plugin. Treat workflow automation as production support for durable food and fitness history.

For every pull request:

1. Apply a semantic version bump before opening the PR:

   ```bash
   python3 scripts/release_workflow.py bump patch --message "Describe the user-visible change."
   ```

   Use `minor` for new user-visible workflows or capabilities and `major` for breaking changes.

2. Run the full test suite:

   ```bash
   python3 -m unittest discover -s tests
   ```

3. Open the PR and wait for CI plus Copilot review.
4. If Copilot requests changes, resolve them at engineering discretion, rerun tests, push, and request another review.
5. Merge only after CI is green and Copilot has no unresolved requested changes. If repository policy blocks a normal merge after review feedback is resolved, the maintainer-approved admin merge path is acceptable.
6. After merge, update local `main`, create the matching release tag, and push it:

   ```bash
   python3 scripts/release_workflow.py tag-release --push
   ```

7. Confirm the release workflow creates the GitHub Release for the tag.

Never tag or release from a dirty worktree or from a commit whose checked-out version does not match `.codex-plugin/plugin.json` and `pyproject.toml`.
