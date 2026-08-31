import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from coverage import classify_with_coverage, nutrient_coverage


class CoverageTests(unittest.TestCase):
    def test_complete_micronutrient_data_has_full_coverage(self):
        rows = [
            {"calories": 400, "iodine_mcg": 100, "nutrient_provenance": {"iodine_mcg": {"tier": "A"}}},
            {"calories": 600, "iodine_mcg": 200, "nutrient_provenance": {"iodine_mcg": {"tier": "B"}}},
        ]
        result = nutrient_coverage(rows, "iodine_mcg")
        self.assertEqual(result["item_weighted"], 1.0)
        self.assertEqual(result["calorie_weighted"], 1.0)
        self.assertEqual(result["confidence_weighted"], 0.95)

    def test_only_twenty_percent_of_calories_known_is_not_a_confident_deficiency(self):
        rows = [
            {"calories": 200, "iodine_mcg": 10, "nutrient_provenance": {"iodine_mcg": {"tier": "B"}}},
            {"calories": 800, "iodine_mcg": None, "nutrient_provenance": {"iodine_mcg": {"tier": "D"}}},
        ]
        coverage = nutrient_coverage(rows, "iodine_mcg")
        self.assertEqual(coverage["calorie_weighted"], 0.2)
        self.assertEqual(classify_with_coverage(10, 150, coverage), "insufficient data coverage to assess")

    def test_missing_is_not_zero_and_unknown_heavy_day_is_gated(self):
        rows = [
            {"calories": 500, "magnesium_mg": None, "nutrient_provenance": {"magnesium_mg": {"tier": "D"}}},
            {"calories": 500, "magnesium_mg": 100, "nutrient_provenance": {"magnesium_mg": {"tier": "C"}}},
        ]
        coverage = nutrient_coverage(rows, "magnesium_mg")
        self.assertEqual(coverage["items_known"], 1)
        self.assertEqual(classify_with_coverage(100, 400, coverage), "insufficient data coverage to assess")

    def test_tombstoned_rows_are_excluded(self):
        rows = [
            {"calories": 500, "potassium_mg": 100, "nutrient_provenance": {"potassium_mg": {"tier": "A"}}},
            {"calories": 500, "potassium_mg": None, "deleted_at": "2026-08-31T12:00:00Z", "nutrient_provenance": {"potassium_mg": {"tier": "D"}}},
        ]
        result = nutrient_coverage(rows, "potassium_mg")
        self.assertEqual(result["items_total"], 1)
        self.assertEqual(result["calorie_weighted"], 1.0)

    def test_well_covered_low_value_is_classified_low(self):
        rows = [{"calories": 100, "iron_mg": 1, "nutrient_provenance": {"iron_mg": {"tier": "B"}}}]
        coverage = nutrient_coverage(rows, "iron_mg")
        self.assertEqual(classify_with_coverage(1, 8, coverage), "intake appears low")


if __name__ == "__main__":
    unittest.main()
