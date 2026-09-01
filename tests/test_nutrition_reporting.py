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
            "targets": {
                "daily_calories": 1900,
                "daily_protein_g": 160,
                "daily_nutrient_targets": {
                    "carbohydrates_g": 170,
                    "fat_g": 65,
                    "fiber_g": 30,
                    "cholesterol_mg": 300,
                    "sodium_mg": 2300,
                    "vitamin_c_mg": 90,
                    "vitamin_d_mcg": 20,
                    "trans_fat_g": 0,
                },
            },
            "nutrient_units": {
                "calories": "kcal", "protein_g": "g", "carbohydrates_g": "g",
                "fat_g": "g", "fiber_g": "g", "water_oz": "fl oz",
            },
            "entries": [
                {"entry_id": "3", "date": "2026-08-30", "meal_category": "snack", "food_product": "Kiwi | gold", "amount_weight": "80 g\nweighed", "calories": 49, "protein_g": 0.9, "carbohydrates_g": 12, "fat_g": 0.4, "fiber_g": 2.4, "water_oz": None, "vitamin_c_mg": 74, "deleted_at": None},
                {"entry_id": "1", "date": "2026-08-30", "meal_category": "breakfast", "food_product": "Eggs", "brand_restaurant_source": "Farm", "amount_weight": "2 large", "calories": 140, "protein_g": 12, "carbohydrates_g": 1, "fat_g": 10, "fiber_g": 0, "water_oz": None, "cholesterol_mg": 372, "deleted_at": None},
                {"entry_id": "2", "date": "2026-08-30", "meal_category": "lunch", "food_product": "Mystery soup", "amount_weight": "1 bowl", "calories": 250, "protein_g": None, "carbohydrates_g": None, "fat_g": None, "fiber_g": None, "water_oz": None, "sodium_mg": 700, "deleted_at": None},
                {"entry_id": "4", "date": "2026-08-30", "meal_category": "drink", "food_product": "Water", "amount_weight": "16 fl oz", "calories": 0, "protein_g": 0, "carbohydrates_g": 0, "fat_g": 0, "fiber_g": 0, "water_oz": 16, "deleted_at": None},
                {"entry_id": "5", "date": "2026-08-31", "meal_category": "breakfast", "food_product": "Toast", "amount_weight": "1 slice", "calories": 100, "protein_g": 4, "carbohydrates_g": 18, "fat_g": 1, "fiber_g": 2, "water_oz": None, "deleted_at": None},
                {"entry_id": "gone", "date": "2026-08-30", "meal_category": "dinner", "food_product": "Deleted food", "calories": 999, "deleted_at": "2026-08-30T12:00:00-04:00"},
            ],
        }

    def test_panel_snapshot_is_deterministic_and_uses_plain_protein(self):
        report = tracker.render_daily_report(self.ledger(), "2026-08-30", view="panel")

        self.assertTrue(report.startswith("Nutrition Panel | 2026-08-30 | America/New_York\n\nDaily Totals\n"))
        self.assertIn("| Metric | Amount | Target |", report)
        self.assertIn("| Food |", report)
        self.assertIn("Micronutrients\n| Nutrient | Amount | DRV % |", report)
        self.assertIn("| Cholesterol | 372.00 mg | 124% |", report)
        self.assertIn("| Sodium | 700.00 mg | 30% |", report)
        self.assertIn("| Vitamin C | 74.00 mg | 82% |", report)
        self.assertIn("| Vitamin B2 (Riboflavin) |", report)
        self.assertIn("| Vitamin B12 (Cobalamin) |", report)
        self.assertNotIn("protein credit", report.lower())

    def test_macro_progress_uses_personal_targets(self):
        report = tracker.render_daily_report(self.ledger(), "2026-08-30", view="panel")

        self.assertIn("| Calories | 439 kcal | 439 kcal / 1,900 kcal (1,461 kcal remaining) |", report)
        self.assertIn("| Protein | 12.90 g | 12.90 g / 160.00 g (147.10 g remaining) |", report)
        self.assertNotIn("Daily Value", report)

    def test_panel_keeps_full_standardized_sections(self):
        report = tracker.render_daily_report(self.ledger(), "2026-08-30", view="panel")

        self.assertLess(report.index("Daily Totals\n| Metric | Amount | Target |"), report.index("Foods\n| Meal | Food | Amount | Calories | Protein | Carbs | Fat | Fiber |"))
        self.assertLess(report.index("Foods\n| Meal | Food | Amount | Calories | Protein | Carbs | Fat | Fiber |"), report.index("Micronutrients\n| Nutrient | Amount | DRV % |"))
        self.assertLess(report.index("Micronutrients\n| Nutrient | Amount | DRV % |"), report.index("Data quality\nActive entries only. Unknown means untracked, not zero."))
        self.assertIn("| Vitamin B7 (Biotin) | unknown | not set |", report)
        self.assertIn("| Vitamin D | unknown | unknown |", report)
        self.assertIn("| Trans fat | unknown | unknown |", report)
        ledger = self.ledger()
        ledger["entries"][0]["trans_fat_g"] = 0.1
        report = tracker.render_daily_report(ledger, "2026-08-30", view="panel")
        self.assertIn("| Trans fat | 0.10 g | above 0 target |", report)

    def test_daily_report_always_contains_item_metrics_meal_subtotals_and_daily_progress(self):
        report = tracker.render_daily_report(self.ledger(), "2026-08-30", view="panel")

        self.assertIn("| Breakfast | Eggs (Farm) | 2 large | 140 kcal | 12.00 g | 1.00 g | 10.00 g | 0.00 g |", report)
        self.assertIn("| Lunch | Mystery soup | 1 bowl | 250 kcal | unknown | unknown | unknown | unknown |", report)
        self.assertIn("| Carbs | 13.00 g | 13.00 g / 170.00 g (157.00 g remaining) |", report)
        self.assertIn("| Fat | 10.40 g | 10.40 g / 65.00 g (54.60 g remaining) |", report)
        self.assertIn("| Fiber | 2.40 g | 2.40 g / 30.00 g (27.60 g remaining) |", report)

    def test_foods_report_contains_item_metrics_and_meal_subtotals(self):
        report = tracker.render_daily_report(self.ledger(), "2026-08-30", view="foods")

        self.assertIn("Daily Totals\n| Metric | Amount | Target |", report)
        self.assertIn("| Breakfast | Eggs (Farm) | 2 large | 140 kcal | 12.00 g | 1.00 g | 10.00 g | 0.00 g |", report)
        self.assertIn("| Lunch | Mystery soup | 1 bowl | 250 kcal | unknown | unknown | unknown | unknown |", report)
        self.assertIn("| Hydration | 473 mL (16.0 fl oz) | tracked drinking water |", report)
        self.assertNotIn("Micronutrients\n", report)

    def test_cli_today_resolves_to_the_configured_local_date_for_read_only_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ledger.json"
            state_path = Path(directory) / "state.json"
            ledger = self.ledger()
            ledger["entries"] = []
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            state_path.write_text("{}\n", encoding="utf-8")
            expected_date = tracker.current_local_date(ledger)
            for command, heading in (("day", '"date":'), ("panel", "Nutrition Panel"), ("foods", "Foods Eaten"), ("daily-totals", "Daily Totals")):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "--ledger", str(ledger_path), "--state", str(state_path), command, "--date", "today"],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                if command == "day":
                    self.assertIn(f'"date": "{expected_date}"', result.stdout)
                else:
                    self.assertTrue(result.stdout.startswith(f"{heading} | {expected_date} | America/New_York"))

    def test_foods_view_reuses_exact_meal_and_food_grammar(self):
        report = tracker.render_daily_report(self.ledger(), "2026-08-30", view="foods")

        self.assertTrue(report.startswith("Foods Eaten | 2026-08-30 | America/New_York\n\nDaily Totals\n"))
        self.assertIn("| Meal | Food | Amount | Calories | Protein | Carbs | Fat | Fiber |", report)
        self.assertLess(report.index("| Breakfast |"), report.index("| Lunch |"))
        self.assertLess(report.index("| Lunch |"), report.index("| Snacks |"))
        self.assertLess(report.index("| Snacks |"), report.index("| Drinks |"))
        self.assertIn("| Snacks | Kiwi \\| gold | 80 g weighed | 49 kcal | 0.90 g | 12.00 g | 0.40 g | 2.40 g |", report)

    def test_empty_day_has_the_same_sections_and_never_invents_zero_foods(self):
        ledger = self.ledger()
        ledger["entries"] = [e for e in ledger["entries"] if e["date"] != "2026-08-31"]
        report = tracker.render_daily_report(ledger, "2026-08-31", view="panel")

        self.assertIn("| Entries | 0 | active foods only |", report)
        self.assertIn("| Hydration | unknown | tracked drinking water |", report)
        self.assertIn("| - | No foods logged | - | unknown | unknown | unknown | unknown | unknown |", report)
        self.assertIn("| Calories | unknown | 0 kcal / 1,900 kcal (1,900 kcal remaining) |", report)

    def test_invalid_report_view_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "panel or foods"):
            tracker.render_daily_report(self.ledger(), "2026-08-30", view="chaos")

    def test_plain_water_is_always_rendered_in_drinks_not_the_meal_where_it_was_logged(self):
        ledger = self.ledger()
        ledger["entries"][-2]["meal_category"] = "breakfast"

        report = tracker.render_daily_report(ledger, "2026-08-30", view="foods")

        self.assertIn("| Breakfast | Eggs (Farm) | 2 large | 140 kcal | 12.00 g | 1.00 g | 10.00 g | 0.00 g |", report)
        self.assertIn("| Drinks | Water | 16 fl oz | 0 kcal | 0.00 g | 0.00 g | 0.00 g | 0.00 g |", report)

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
                self.assertTrue(result.stdout.startswith(f"{heading} | 2026-08-30 | America/New_York"))
                self.assertIn("Data quality\nActive entries only. Unknown means untracked, not zero.", result.stdout)

    def test_daily_totals_uses_standard_table_contract(self):
        report = tracker.render_daily_totals(self.ledger(), "2026-08-30")

        self.assertEqual(report.splitlines()[:4], [
            "Daily Totals | 2026-08-30 | America/New_York",
            "",
            "| Metric | Amount | Target |",
            "| --- | --- | --- |",
        ])
        self.assertIn("| Calories | 439 kcal | 439 kcal / 1,900 kcal (1,461 kcal remaining) |", report)

    def test_weekly_totals_uses_standard_daily_and_nutrient_tables(self):
        report = tracker.render_weekly_totals(self.ledger(), "2026-08-30", "2026-08-31")

        self.assertTrue(report.startswith("Weekly Totals | 2026-08-30 to 2026-08-31 | America/New_York\n\nDaily Rows\n"))
        self.assertIn("| Date | Entries | Calories | Protein | Carbs | Fat | Fiber | Hydration |", report)
        self.assertIn("| 2026-08-30 | 4 | 439 kcal | 12.90 g | 13.00 g | 10.40 g | 2.40 g | 16.0 fl oz |", report)
        self.assertIn("| 2026-08-31 | 1 | 100 kcal | 4.00 g | 18.00 g | 1.00 g | 2.00 g | unknown |", report)
        self.assertIn("Weekly Totals\n| Metric | Amount | Target |", report)
        self.assertIn("Micronutrients\n| Nutrient | Amount | DRV % |", report)
        self.assertIn("| Cholesterol | 372.00 mg | 124% |", report)
        self.assertIn("| Sodium | 700.00 mg | 30% |", report)
        self.assertIn("| Vitamin C | 74.00 mg | 82% |", report)


if __name__ == "__main__":
    unittest.main()
