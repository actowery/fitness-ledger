import importlib.util
import json
from pathlib import Path
from unittest import mock
import unittest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "release_workflow.py"
SPEC = importlib.util.spec_from_file_location("release_workflow", SCRIPT)
release_workflow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_workflow)


class ReleaseWorkflowTests(unittest.TestCase):
    def test_semver_bump_rules(self) -> None:
        self.assertEqual(release_workflow.bump_version("1.2.3", "patch"), "1.2.4")
        self.assertEqual(release_workflow.bump_version("1.2.3", "minor"), "1.3.0")
        self.assertEqual(release_workflow.bump_version("1.2.3", "major"), "2.0.0")

    def test_invalid_semver_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "semantic"):
            release_workflow.parse_version("1.2")

    def test_pr_version_must_increase_from_base(self) -> None:
        with (
            mock.patch.object(release_workflow, "ensure_versions_match", return_value="1.2.0"),
            mock.patch.object(release_workflow, "base_manifest_version", return_value="1.2.0"),
            mock.patch.object(release_workflow, "changelog_has_version", return_value=True),
        ):
            with self.assertRaisesRegex(ValueError, "must increase"):
                release_workflow.check_pr_version("origin/main")

    def test_pr_version_requires_changelog_entry(self) -> None:
        with (
            mock.patch.object(release_workflow, "ensure_versions_match", return_value="1.2.1"),
            mock.patch.object(release_workflow, "base_manifest_version", return_value="1.2.0"),
            mock.patch.object(release_workflow, "changelog_has_version", return_value=False),
        ):
            with self.assertRaisesRegex(ValueError, "CHANGELOG"):
                release_workflow.check_pr_version("origin/main")

    def test_pr_version_accepts_increased_version_with_changelog(self) -> None:
        with (
            mock.patch.object(release_workflow, "ensure_versions_match", return_value="1.2.1"),
            mock.patch.object(release_workflow, "base_manifest_version", return_value="1.2.0"),
            mock.patch.object(release_workflow, "changelog_has_version", return_value=True),
        ):
            release_workflow.check_pr_version("origin/main")

    def test_release_script_can_create_tag_and_release(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("tag-release", text)
        self.assertIn("gh\", \"release\", \"create\"", text)
        self.assertIn("v{version}", text)

    def test_create_release_requires_pushing_the_tag(self) -> None:
        with self.assertRaisesRegex(ValueError, "--create-release requires --push"):
            release_workflow.validate_tag_release_options(push=False, create_release=True)

        release_workflow.validate_tag_release_options(push=True, create_release=True)

    def test_review_gate_fails_on_copilot_recommendations(self) -> None:
        response = {"headRefOid": "abc", "reviews": [{"author": {"login": "copilot-pull-request-reviewer"}, "commit": {"oid": "abc"}, "submittedAt": "2026-09-02T00:00:00Z", "body": "### Changes recommended"}]}
        with mock.patch("subprocess.run", return_value=mock.Mock(stdout=json.dumps(response))):
            with self.assertRaisesRegex(ValueError, "recommends changes"):
                release_workflow.wait_for_copilot_review("1", wait_minutes=0, poll_seconds=0)

    def test_review_gate_rejects_review_for_old_head(self) -> None:
        response = {"headRefOid": "new", "reviews": [{"author": {"login": "copilot-pull-request-reviewer"}, "commit": {"oid": "old"}, "body": ""}]}
        with mock.patch("subprocess.run", return_value=mock.Mock(stdout=json.dumps(response))):
            with self.assertRaisesRegex(TimeoutError, "did not complete"):
                release_workflow.wait_for_copilot_review("1", wait_minutes=0, poll_seconds=0)

    def test_review_gate_accepts_current_head_review_immediately(self) -> None:
        response = {"headRefOid": "abc", "reviews": [{"author": {"login": "copilot-pull-request-reviewer"}, "commit": {"oid": "abc"}, "submittedAt": "2026-09-02T00:00:00Z", "body": "### Looks good"}]}
        with mock.patch("subprocess.run", return_value=mock.Mock(stdout=json.dumps(response))):
            with mock.patch.object(release_workflow.time, "sleep") as sleep:
                release_workflow.wait_for_copilot_review("1", wait_minutes=5, poll_seconds=0)
                sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
