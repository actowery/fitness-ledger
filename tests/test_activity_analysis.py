import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from activity_analysis import compare_training_rest, pre_workout_rows


class ActivityAnalysisTests(unittest.TestCase):
    def test_pre_workout_window_excludes_future_entries(self):
        workout = datetime(2026, 8, 31, 16, tzinfo=timezone.utc)
        rows = [
            {"food_product": "before", "logged_at": "2026-08-31T14:00:00Z"},
            {"food_product": "after", "logged_at": "2026-08-31T17:00:00Z"},
        ]
        self.assertEqual([r["food_product"] for r in pre_workout_rows(rows, workout, 24)], ["before"])

    def test_pre_workout_excludes_tombstones(self):
        workout = datetime(2026, 8, 31, 16, tzinfo=timezone.utc)
        rows = [{"food_product": "deleted", "logged_at": "2026-08-31T14:00:00Z", "deleted_at": "2026-08-31T15:00:00Z"}]
        self.assertEqual(pre_workout_rows(rows, workout, 24), [])

    def test_training_rest_comparison_is_descriptive_not_causal(self):
        result = compare_training_rest([
            {"training_day": True, "protein_g": 150}, {"training_day": False, "protein_g": 120}
        ], "protein_g")
        self.assertEqual(result["training_mean"], 150)
        self.assertEqual(result["rest_mean"], 120)
        self.assertEqual(result["interpretation"], "associated with")

    def test_missing_group_is_insufficient_evidence(self):
        result = compare_training_rest([{ "training_day": True, "calories": 2000 }], "calories")
        self.assertEqual(result["interpretation"], "insufficient evidence")


if __name__ == "__main__":
    unittest.main()
