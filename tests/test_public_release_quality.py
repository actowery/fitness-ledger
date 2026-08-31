"""Release gates for a distributable, skills-only Fitness Ledger plugin."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
FORBIDDEN_MARKERS = (
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

    def test_manifest_metadata_meets_public_directory_limits(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        interface = manifest["interface"]
        self.assertLessEqual(len(interface["displayName"]), 30)
        self.assertLessEqual(len(interface["shortDescription"]), 30)
        self.assertLessEqual(len(interface["longDescription"]), 4000)
        self.assertLessEqual(len(interface["developerName"]), 80)
        self.assertIn(
            interface["category"],
            {
                "Productivity",
                "Creativity",
                "Developer Tools",
                "Business & Operations",
                "Data & Analytics",
                "Communication",
                "Education & Research",
                "Security",
                "Finance",
                "Healthcare",
                "Travel",
                "Entertainment",
                "Other",
            },
        )
        for field in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
            self.assertTrue(interface[field].startswith("https://"))
            self.assertLessEqual(len(interface[field]), 1024)
        for field in ("logo", "composerIcon"):
            asset = interface[field]
            self.assertTrue(asset.startswith("./assets/"))
            self.assertTrue((ROOT / asset.removeprefix("./")).is_file())
        prompts = interface["defaultPrompt"]
        self.assertIsInstance(prompts, list)
        self.assertGreaterEqual(len(prompts), 1)
        self.assertLessEqual(len(prompts), 3)
        self.assertEqual(len(prompts), len(set(prompts)))
        for prompt in prompts:
            self.assertLessEqual(len(prompt), 128)
            self.assertNotIn("\n", prompt)

    def test_package_and_plugin_versions_match(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version = "([^"]+)"$', project, flags=re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), manifest["version"])

    def test_skills_are_library_native_and_do_not_require_local_runtime_execution(self) -> None:
        nutrition = (ROOT / "skills" / "nutrition-ledger" / "SKILL.md").read_text(encoding="utf-8")
        fitness = (ROOT / "skills" / "fitness-sync" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("ChatGPT Library", nutrition)
        self.assertIn("never require a local filesystem path, a local process", nutrition)
        self.assertIn("offline developer/test reference", nutrition)
        self.assertIn("ChatGPT Library", fitness)
        self.assertIn("must not depend on launching a local process", fitness)
        self.assertIn("when those sources are connected", fitness)
        self.assertIn("user-provided snapshots", fitness)
        self.assertIn("offline developer/test reference", fitness)
        self.assertNotIn("python3 scripts/nutrition_tracker.py", nutrition)
        self.assertNotIn("python3 scripts/fitness_sync.py", fitness)

    def test_library_persistence_contract_is_bundled_and_referenced(self) -> None:
        contract = ROOT / "skills" / "nutrition-ledger" / "references" / "library-contract.md"
        self.assertTrue(contract.is_file())
        text = contract.read_text(encoding="utf-8")
        for required in ("current-version guard", "No partial mutation", "Fitness_Ledger_Nutrition_Ledger.json"):
            self.assertIn(required, text)
        self.assertIn("never duplicate or rename", text)
        fitness = (ROOT / "skills" / "fitness-sync" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Library persistence contract", fitness)

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

    def test_release_workflow_requires_a_versioned_tag_and_creates_a_github_release(self) -> None:
        workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("tags: ['v*']", workflow)
        self.assertIn("python3 -m unittest discover -v -s tests", workflow)
        self.assertIn("Validate tag matches plugin version", workflow)
        self.assertIn("gh release create", workflow)

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
            "TERMS.md",
            "SUPPORT.md",
            "SECURITY.md",
            "LICENSE",
            "CONTRIBUTING.md",
            "PLUGIN_TEST_MATRIX.md",
            "PUBLIC_SUBMISSION.md",
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
