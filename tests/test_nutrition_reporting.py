import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import unittest


SCRIPT = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts" / "nutrition_tracker.py"
SPEC = importlib.util.spec_from_file_location("nutrition_tracker_reporting", SCRIPT)
tracker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tracker)


class NutritionReportingTests(unittest.TestCase):
    def ledger(self):
        return {
            "timezone": "America/New_York",
            "targets": {"daily_calories": 1900, "daily_protein_g": 160},
            "nutrient_units": {
                "calories": "kcal", "protein_g": "g", "carbohydrates_g": "g",
                "fat_g": "g", "fiber_g": "g", "water_oz": "fl oz",
            },
            "entries": [
                {"entry_id": "3", "date": "2026-08-30", "meal_category": "snack", "food_product": "Kiwi", "amount_weight": "80 g", "calories": 49, "protein_g": 0.9, "carbohydrates_g": 12, "fat_g": 0.4, "fiber_g": 2.4, "water_oz": None, "deleted_at": None},
                {"entry_id": "1", "date": "2026-08-30", "meal_category": "breakfast", "food_product": "Eggs", "brand_restaurant_source": "Farm", "amount_weight": "2 large", "calories": 140, "protein_g": 12, "carbohydrates_g": 1, "fat_g": 10, "fiber_g": 0, "water_oz": None, "deleted_at": None},
                {"entry_id": "2", "date": "2026-08-30", "meal_category": "lunch", "food_product": "Mystery soup", "amount_weight": "1 bowl", "calories": 250, "protein_g": None, "carbohydrates_g": None, "fat_g": None, "fiber_g": None, "water_oz": None, "deleted_at": None},
                {"entry_id": "4", "date": "2026-08-30", "meal_category": "drink", "food_product": "Water", "amount_weight": "16 fl oz", "calories": 0, "protein_g": 0, "carbohydrates_g": 0, "fat_g": 0, "fiber_g": 0, "water_oz": 16, "deleted_at": None},
                {"entry_id": "gone", "date": "2026-08-30", "meal_category": "dinner", "food_product": "Deleted food", "calories": 999, "deleted_at": "2026-08-30T12:00:00-04:00"},
            ],
        }

    def test_panel_snapshot_is_deterministic_and_uses_plain_protein(self):
        report = tracker.render_daily_report(self.ledger(), "2026-08-30", view="panel")

        self.assertEqual(report, """Nutrition Panel — 2026-08-30 (America/New_York)
Entries: 4 | Weight: not logged

Progress
Calories: 439 / 1,900 kcal (1,461 remaining)
Protein: 12.9 / 160.0 g (147.1 remaining)
Carbs: 13.0 g | Fat: 10.4 g | Fiber: 2.4 g
Hydration: 473 mL (16.0 fl oz)

Meals
Breakfast — 1 item | 140 kcal | P 12.0 g
- Eggs (Farm), 2 large — 140 kcal | P 12.0 g | C 1.0 g | F 10.0 g | Fi 0.0 g
Lunch — 1 item | 250 kcal | P unknown
- Mystery soup, 1 bowl — 250 kcal | P unknown | C unknown | F unknown | Fi unknown
Snacks — 1 item | 49 kcal | P 0.9 g
- Kiwi, 80 g — 49 kcal | P 0.9 g | C 12.0 g | F 0.4 g | Fi 2.4 g
Drinks — 1 item | 0 kcal | P 0.0 g
- Water, 16 fl oz — 0 kcal | P 0.0 g | C 0.0 g | F 0.0 g | Fi 0.0 g

Data quality
Active entries only. Unknown means untracked, not zero.""")
        self.assertNotIn("protein credit", report.lower())

    def test_progress_uses_personal_targets_not_generic_daily_values(self):
        report = tracker.render_daily_report(self.ledger(), "2026-08-30", view="panel")

        self.assertIn("Calories: 439 / 1,900 kcal (1,461 remaining)", report)
        self.assertIn("Protein: 12.9 / 160.0 g (147.1 remaining)", report)
        self.assertNotIn("58%", report)
        self.assertNotIn("Daily Value", report)

    def test_foods_view_reuses_exact_meal_and_food_grammar(self):
        report = tracker.render_daily_report(self.ledger(), "2026-08-30", view="foods")

        self.assertTrue(report.startswith("Foods Eaten — 2026-08-30 (America/New_York)\nEntries: 4 | Weight: not logged\n\nMeals\n"))
        self.assertIn("Breakfast — 1 item | 140 kcal | P 12.0 g\n- Eggs (Farm), 2 large", report)
        self.assertLess(report.index("Breakfast —"), report.index("Lunch —"))
        self.assertLess(report.index("Lunch —"), report.index("Snacks —"))
        self.assertLess(report.index("Snacks —"), report.index("Drinks —"))
        self.assertNotIn("Progress\n", report)

    def test_empty_day_has_the_same_sections_and_never_invents_zero_foods(self):
        report = tracker.render_daily_report(self.ledger(), "2026-08-31", view="panel")

        self.assertIn("Entries: 0 | Weight: not logged", report)
        self.assertIn("Hydration: not logged", report)
        self.assertIn("Meals\nNo foods logged.", report)
        self.assertIn("Calories: 0 / 1,900 kcal (1,900 remaining)", report)

    def test_invalid_report_view_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "panel or foods"):
            tracker.render_daily_report(self.ledger(), "2026-08-30", view="chaos")

    def test_plain_water_is_always_rendered_in_drinks_not_the_meal_where_it_was_logged(self):
        ledger = self.ledger()
        ledger["entries"][-2]["meal_category"] = "breakfast"

        report = tracker.render_daily_report(ledger, "2026-08-30", view="foods")

        self.assertIn("Breakfast — 1 item | 140 kcal | P 12.0 g", report)
        self.assertIn("Drinks — 1 item | 0 kcal | P 0.0 g", report)

    def test_cli_panel_and_foods_are_routed_through_the_canonical_renderer(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ledger.json"
            state_path = Path(directory) / "state.json"
            ledger_path.write_text(json.dumps(self.ledger()), encoding="utf-8")
            state_path.write_text("{}\n", encoding="utf-8")
            for command, heading in (("panel", "Nutrition Panel"), ("foods", "Foods Eaten")):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "--ledger", str(ledger_path), "--state", str(state_path), command, "--date", "2026-08-30"],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(result.stdout.startswith(f"{heading} — 2026-08-30 (America/New_York)"))
                self.assertIn("Data quality\nActive entries only. Unknown means untracked, not zero.", result.stdout)


if __name__ == "__main__":
    unittest.main()
