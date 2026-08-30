import importlib.util
import copy
from pathlib import Path

import unittest


SCRIPT = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts" / "nutrition_tracker.py"
SPEC = importlib.util.spec_from_file_location("nutrition_tracker_validation", SCRIPT)
tracker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tracker)


class NutritionValidationTests(unittest.TestCase):
    def base_ledger(self, entry):
        return {
            "schema_version": "1.0.0",
            "entries": [entry],
            "weights": [],
            "food_master": [],
        }

    def test_validation_rejects_malformed_entry_date(self):
        errors = tracker.validate(self.base_ledger({"entry_id": "1", "date": "08/30/2026", "food_product": "x"}))

        self.assertTrue(any("invalid date" in error for error in errors))

    def test_validation_rejects_negative_nutrition_values(self):
        errors = tracker.validate(self.base_ledger({
            "entry_id": "1", "date": "2026-08-30", "food_product": "x",
            "calories": -1, "protein_g": -2, "carbohydrates_g": 0, "fat_g": 0, "fiber_g": 0,
        }))

        self.assertTrue(any("negative calories" in error for error in errors))
        self.assertTrue(any("negative protein_g" in error for error in errors))

    def test_validation_rejects_negative_quantity(self):
        errors = tracker.validate(self.base_ledger({
            "entry_id": "1", "date": "2026-08-30", "food_product": "x", "quantity": -1,
        }))

        self.assertTrue(any("negative quantity" in error for error in errors))

    def test_v2_validation_requires_food_master_id_on_every_entry(self):
        ledger = {
            "schema_version": "2.0.0",
            "nutrient_units": {"calories": "kcal"},
            "entries": [{"entry_id": "1", "date": "2026-08-30", "food_product": "x", "calories": None,
                         "nutrient_provenance": {"calories": {"tier": "D"}}}],
            "weights": [], "food_master": [],
        }

        errors = tracker.validate(ledger)

        self.assertTrue(any("missing food_master_id" in error for error in errors))

    def test_missing_nutrient_is_not_zero_and_explicit_zero_is_valid(self):
        missing = self.base_ledger({"entry_id": "1", "date": "2026-08-30", "food_product": "x", "calories": None})
        explicit_zero = self.base_ledger({"entry_id": "1", "date": "2026-08-30", "food_product": "x", "calories": 0})

        self.assertIsNone(missing["entries"][0]["calories"])
        self.assertNotIn("negative calories", tracker.validate(explicit_zero))

    def test_daily_cache_fingerprint_mismatch_is_detected(self):
        ledger = self.base_ledger({"entry_id": "1", "date": "2026-08-30", "food_product": "x", "calories": 10})
        ledger["daily_cache"] = {"2026-08-30": {"ledger_fingerprint": "stale"}}

        self.assertFalse(tracker.cache_matches(ledger, "2026-08-30"))

    def test_persisted_state_must_match_current_ledger_and_cache(self):
        ledger = self.base_ledger({"entry_id": "1", "date": "2026-08-30", "food_product": "x", "calories": 10})
        fingerprint = tracker.ledger_fingerprint(ledger, "2026-08-30")
        ledger["daily_cache"] = {"2026-08-30": {"ledger_fingerprint": fingerprint}}
        state = {"current_date": "2026-08-30", "ledger_fingerprint": fingerprint}

        self.assertTrue(tracker.state_matches(ledger, state, "2026-08-30"))
        state["ledger_fingerprint"] = "stale"
        self.assertFalse(tracker.state_matches(ledger, state, "2026-08-30"))

    def test_correction_preserves_before_snapshot_and_entry_identity(self):
        entry = {"entry_id": "E-1", "date": "2026-08-30", "food_product": "old", "calories": 100, "revision": 1}
        ledger = self.base_ledger(entry)
        ledger["audit_log"] = []

        tracker.correct_entry(ledger, "E-1", {"food_product": "new", "calories": 120}, "2026-08-30T12:00:00-04:00")

        self.assertEqual(ledger["entries"][0]["entry_id"], "E-1")
        self.assertEqual(ledger["entries"][0]["revision"], 2)
        self.assertEqual(ledger["audit_log"][-1]["before"]["calories"], 100)
        self.assertEqual(ledger["audit_log"][-1]["after"]["calories"], 120)

    def test_tombstone_preserves_history_but_removes_entry_from_totals(self):
        ledger = self.base_ledger({"entry_id": "E-1", "date": "2026-08-30", "food_product": "x", "calories": 100, "revision": 1, "deleted_at": None})
        ledger["audit_log"] = []

        tracker.tombstone_entry(ledger, "E-1", "2026-08-30T12:00:00-04:00")

        totals, rows = tracker.totals_for(ledger, "2026-08-30")
        self.assertEqual(rows, [])
        self.assertEqual(ledger["entries"][0]["entry_id"], "E-1")
        self.assertIsNotNone(ledger["entries"][0]["deleted_at"])
        self.assertEqual(ledger["audit_log"][-1]["event"], "entry_tombstoned")

    def test_repeated_food_master_upsert_is_idempotent(self):
        ledger = {"food_master": []}
        record = {"food_name": "same food", "brand": "same brand"}

        first = tracker.upsert_food_master(ledger, copy.deepcopy(record))
        second = tracker.upsert_food_master(ledger, copy.deepcopy(record))

        self.assertEqual(first["food_master_id"], second["food_master_id"])
        self.assertEqual(len(ledger["food_master"]), 1)


if __name__ == "__main__":
    unittest.main()
