"""Release gates for a distributable, skills-only Fitness Ledger plugin."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
FORBIDDEN_MARKERS = (
    "Battle Mage",
    "/workspace/",
    "/root/.codex",
    "libfile_",
    "tracker_files",
)


class PublicReleaseQualityTests(unittest.TestCase):
    def test_manifest_declares_a_skills_only_plugin(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "fitness-ledger")
        self.assertTrue(manifest["version"])
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("apps", manifest)
        self.assertNotEqual(manifest["author"]["name"], "Local developer")

    def test_repo_marketplace_exposes_the_plugin_from_github(self) -> None:
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        self.assertEqual(marketplace["name"], "fitness-ledger-marketplace")
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "fitness-ledger")
        self.assertEqual(entry["source"]["source"], "url")
        self.assertEqual(entry["source"]["url"], "https://github.com/actowery/fitness-ledger.git")
        self.assertEqual(entry["source"]["ref"], "main")
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")

    def test_ci_runs_on_pushes_and_pull_requests(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pull_request:", workflow)
        self.assertIn("push:", workflow)
        self.assertIn("python3 -m unittest discover -v -s tests", workflow)
        self.assertIn("python3 -m json.tool .codex-plugin/plugin.json", workflow)

    def test_bundle_has_no_personal_paths_or_identifiers(self) -> None:
        ignored = {".git", "__pycache__"}
        for path in ROOT.rglob("*"):
            if (
                not path.is_file()
                or ignored.intersection(path.parts)
                or path == Path(__file__)
            ):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in FORBIDDEN_MARKERS:
                self.assertNotIn(marker, text, f"{marker!r} leaked into {path.relative_to(ROOT)}")

    def test_release_material_is_present(self) -> None:
        for filename in (
            "README.md",
            "PRIVACY.md",
            "SECURITY.md",
            "LICENSE",
            "CONTRIBUTING.md",
            "PLUGIN_TEST_MATRIX.md",
            "RELEASE_CHECKLIST.md",
            "examples/sample_ledger.json",
        ):
            self.assertTrue((ROOT / filename).is_file(), filename)

    def test_license_is_permissive_mit_with_attribution(self) -> None:
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(license_text.startswith("MIT License"))
        self.assertIn("shall be included in all copies", license_text)

    def test_target_free_sample_ledger_is_valid(self) -> None:
        sample = json.loads((ROOT / "examples/sample_ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(sample["targets"], {})

    def test_gitignore_allows_manifest_and_public_fixtures(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertNotIn("*.json", gitignore)
        self.assertIn("nutrition_ledger.json", gitignore)


if __name__ == "__main__":
    unittest.main()
