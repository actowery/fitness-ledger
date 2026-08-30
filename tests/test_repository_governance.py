"""Regression tests for repository-managed security controls."""

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class RepositoryGovernanceTests(unittest.TestCase):
    def test_security_critical_files_have_a_maintainer_code_owner(self) -> None:
        codeowners = (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
        self.assertIn("/.github/workflows/ @actowery", codeowners)
        self.assertIn("/.codex-plugin/ @actowery", codeowners)
        self.assertIn("/skills/ @actowery", codeowners)

    def test_dependabot_tracks_github_actions_updates(self) -> None:
        dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        self.assertIn('package-ecosystem: "github-actions"', dependabot)
        self.assertIn('directory: "/"', dependabot)

    def test_workflows_pin_third_party_actions_by_commit_sha(self) -> None:
        for filename in ("ci.yml", "release.yml"):
            workflow = (ROOT / ".github" / "workflows" / filename).read_text(encoding="utf-8")
            self.assertIn("actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683", workflow)
            self.assertIn("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065", workflow)


if __name__ == "__main__":
    unittest.main()
