import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from enrichment import select_nutrients


class EnrichmentTests(unittest.TestCase):
    def test_reported_label_value_wins_over_conflicting_analogue(self):
        result = select_nutrients({"calories": 200}, {"calories": 230, "magnesium_mg": 40})
        self.assertEqual(result["calories"]["selected_value"], 200)
        self.assertEqual(result["calories"]["confidence_tier"], "A")
        self.assertEqual(result["magnesium_mg"]["selected_value"], 40)
        self.assertEqual(result["magnesium_mg"]["confidence_tier"], "C")

    def test_missing_label_nutrient_is_enriched_but_remains_distinguishable(self):
        result = select_nutrients({"protein_g": 30}, {"protein_g": 31, "manganese_mg": 0.2})
        self.assertIsNone(result["manganese_mg"]["reported_value"])
        self.assertEqual(result["manganese_mg"]["selection_reason"], "fills missing reported nutrient")

    def test_user_override_is_explicit(self):
        result = select_nutrients({"sodium_mg": 200}, {"sodium_mg": 150}, overrides={"sodium_mg": 180})
        self.assertEqual(result["sodium_mg"]["selected_value"], 180)
        self.assertEqual(result["sodium_mg"]["selection_reason"], "explicit user override")

    def test_unknown_remains_unknown(self):
        result = select_nutrients({}, {})
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
