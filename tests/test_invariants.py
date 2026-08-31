import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from invariants import review_queue, validate_nutrition_record


class NutritionInvariantTests(unittest.TestCase):
    def test_saturated_fat_cannot_exceed_total_fat(self):
        issues = validate_nutrition_record({"fat_g": 5, "saturated_fat_g": 6})
        self.assertTrue(any(i["code"] == "saturated_exceeds_fat" for i in issues))

    def test_added_sugar_cannot_exceed_total_sugar(self):
        issues = validate_nutrition_record({"total_sugars_g": 5, "added_sugars_g": 6})
        self.assertTrue(any(i["code"] == "added_exceeds_total_sugar" for i in issues))

    def test_negative_nan_and_infinite_values_are_errors(self):
        issues = validate_nutrition_record({"calories": -1, "protein_g": float("nan"), "fat_g": float("inf")})
        self.assertEqual(sum(i["code"] == "invalid_numeric" for i in issues), 3)

    def test_calorie_mismatch_is_reviewable_but_not_overly_strict(self):
        issues = validate_nutrition_record({"calories": 300, "protein_g": 10, "carbohydrates_g": 10, "fat_g": 10})
        self.assertTrue(any(i["code"] == "macro_calorie_mismatch" and i["severity"] == "warning" for i in issues))
        self.assertEqual(validate_nutrition_record({"calories": 100, "protein_g": 10, "carbohydrates_g": 10, "fat_g": 0}), [])

    def test_review_queue_is_structured_and_keeps_entry_identity(self):
        queue = review_queue([{"entry_id": "e-1", "calories": -2}, {"entry_id": "e-2", "calories": 100}])
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["entry_id"], "e-1")


if __name__ == "__main__":
    unittest.main()
