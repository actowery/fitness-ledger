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
        workflow_dir = ROOT / ".github" / "workflows"
        workflow_paths = sorted(workflow_dir.glob("*.yml"))
        self.assertTrue(workflow_paths)
        for workflow_path in workflow_paths:
            for line in workflow_path.read_text(encoding="utf-8").splitlines():
                if "uses:" not in line:
                    continue
                action_ref = line.split("uses:", 1)[1].split("#", 1)[0].strip()
                if action_ref.startswith("./"):
                    continue
                self.assertRegex(
                    action_ref,
                    r"^[^/\s]+/[^@\s]+@[0-9a-f]{40}$",
                    f"Unpinned workflow action in {workflow_path.name}: {action_ref}",
                )


if __name__ == "__main__":
    unittest.main()
