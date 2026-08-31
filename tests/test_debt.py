import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from debt import prioritize_food_master_debt


class FoodMasterDebtTests(unittest.TestCase):
    NOW = datetime(2026, 8, 31, tzinfo=timezone.utc)

    def test_frequently_used_sparse_master_ranks_first(self):
        masters = [{"food_master_id": "often", "magnesium_mg": None, "last_verified_at": "2026-08-01T00:00:00Z"}, {"food_master_id": "rare", "magnesium_mg": None, "last_verified_at": "2026-08-01T00:00:00Z"}]
        entries = [{"food_master_id": "often", "calories": 100}] * 5 + [{"food_master_id": "rare", "calories": 100}]
        result = prioritize_food_master_debt(masters, entries, now=self.NOW)
        self.assertEqual(result[0]["food_master_id"], "often")

    def test_well_characterized_master_ranks_below_sparse_stale_master(self):
        masters = [{"food_master_id": "good", "calories": 100, "protein_g": 10, "fat_g": 2, "last_verified_at": "2026-08-01T00:00:00Z"}, {"food_master_id": "stale", "magnesium_mg": None, "last_verified_at": "2025-01-01T00:00:00Z"}]
        result = prioritize_food_master_debt(masters, [{"food_master_id": "good", "calories": 100}, {"food_master_id": "stale", "calories": 100}], now=self.NOW)
        self.assertEqual(result[0]["food_master_id"], "stale")


if __name__ == "__main__": unittest.main()
