import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from contributions import top_sources
from longitudinal import summarize_window


class LongitudinalAndContributionTests(unittest.TestCase):
    def test_window_reports_mean_median_range_and_target_frequency(self):
        rows = [{"calories": 500, "potassium_mg": 100}, {"calories": 500, "potassium_mg": 300}]
        result = summarize_window(rows, "potassium_mg", target=200)
        self.assertEqual(result["mean"], 200.0)
        self.assertEqual(result["median"], 200.0)
        self.assertEqual(result["target_hit_frequency"], 0.5)
        self.assertEqual(result["interpretation"], "adequate trend")

    def test_sparse_window_exposes_insufficient_coverage(self):
        rows = [{"calories": 100, "iodine_mcg": 10}, {"calories": 900, "iodine_mcg": None}]
        result = summarize_window(rows, "iodine_mcg", target=150)
        self.assertEqual(result["interpretation"], "insufficient data coverage to assess")

    def test_contribution_excludes_unknown_tombstones_and_duplicates_are_aggregated(self):
        rows = [
            {"food_product": "milk", "potassium_mg": 200},
            {"food_product": "milk", "potassium_mg": 100},
            {"food_product": "banana", "potassium_mg": None},
            {"food_product": "old", "potassium_mg": 1000, "deleted_at": "2026-08-30T00:00:00Z"},
        ]
        result = top_sources(rows, "potassium_mg")
        self.assertEqual(result[0], {"food": "milk", "amount": 300.0, "proportion": 1.0})

    def test_contribution_order_is_deterministic(self):
        rows = [{"food_product": "b", "iron_mg": 2}, {"food_product": "a", "iron_mg": 2}]
        self.assertEqual([r["food"] for r in top_sources(rows, "iron_mg")], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
