"""Regression gates for canon-first nutrition reporting."""

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "nutrition-ledger" / "SKILL.md"
CONTRACT = ROOT / "skills" / "nutrition-ledger" / "references" / "library-contract.md"


class CanonFirstContractTests(unittest.TestCase):
    def test_skill_requires_canonical_read_before_current_state(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("Canon-first is mandatory", text)
        self.assertIn(
            "resolve and read the canonical ledger before reading `Fitness_Ledger_Nutrition_Current_State.json`",
            text,
        )
        self.assertIn("canonical active entries win", text)
        self.assertIn("Never answer “show today’s foods”", text)

    def test_daily_report_contract_cannot_under_report_from_stale_cache(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("`Current_State` is never the primary read source", text)
        self.assertIn("include the canonical item in the report", text)
        self.assertIn("mark/rebuild the state as stale", text)

    def test_library_contract_makes_cache_disagreement_a_repair_event(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("canonical history wins", text)
        self.assertIn("never silently omit a canonical item", text)
        self.assertIn("A stale cache is a cache-repair event", text)
        self.assertIn("canonical history is the mandatory first read", text)

    def test_installation_guard_preserves_existing_identity_and_history(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        required = (
            "Installing or upgrading this public skill is not a data migration",
            "preserve that path and identity",
            "read-only continuity check",
            "Never replay, import, or re-log existing history",
            "Do not delete, rename, merge, or overwrite same-named non-canonical snapshots",
            "do not create a duplicate entry",
        )
        for phrase in required:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
