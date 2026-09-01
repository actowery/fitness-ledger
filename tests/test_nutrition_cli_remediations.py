import json
from pathlib import Path
import subprocess
import sys
import tempfile

import unittest


SCRIPT = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts" / "nutrition_tracker.py"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def provenance(tier="A"):
    return {
        field: {
            "tier": tier,
            "source_type": "test",
            "source_id": "test",
            "method": "direct",
            "verified_at": "2026-09-01T00:00:00-04:00",
        }
        for field in ("calories", "protein_g", "protein_credit_g", "carbohydrates_g", "fat_g", "fiber_g")
    }


class NutritionCliRemediationTests(unittest.TestCase):
    def ledger(self):
        return {
            "schema_version": "2.1.0",
            "tracker_id": "test-ledger",
            "timezone": "America/New_York",
            "targets": {"daily_calories": 1900, "daily_protein_g": 160},
            "nutrient_units": {
                "calories": "kcal",
                "protein_g": "g",
                "protein_credit_g": "g",
                "carbohydrates_g": "g",
                "fat_g": "g",
                "fiber_g": "g",
            },
            "sync": {"pending_excel_sync": False},
            "entries": [
                {
                    "entry_id": "20260901-001",
                    "date": "2026-09-01",
                    "meal_category": "breakfast",
                    "food_product": "Eggs",
                    "amount_weight": "2 large",
                    "calories": 140,
                    "protein_g": 12,
                    "protein_credit_g": 12,
                    "carbohydrates_g": 1,
                    "fat_g": 10,
                    "fiber_g": 0,
                    "food_master_id": "FM-EGGS",
                    "nutrient_provenance": provenance(),
                    "deleted_at": None,
                }
            ],
            "weights": [],
            "food_master": [
                {
                    "food_master_id": "FM-PLUM",
                    "food_name": "Red plum, raw",
                    "brand": "USDA FoodData Central",
                    "serving_description": "130 g",
                    "serving_weight_g": 130,
                    "nutrients": {
                        "calories": 59.8,
                        "protein_g": 0.91,
                        "protein_credit_g": 0.91,
                        "carbohydrates_g": 14.85,
                        "fat_g": 0.36,
                        "fiber_g": 1.82,
                    },
                    "nutrient_provenance": provenance("B"),
                    "source_type": "authoritative_reference",
                    "source_url_or_id": "USDA FDC 169949",
                    "active": True,
                }
            ],
        }

    def write_ledger(self, directory):
        ledger_path = Path(directory) / "Fitness_Ledger_Nutrition_Ledger.json"
        ledger_path.write_text(json.dumps(self.ledger()), encoding="utf-8")
        return ledger_path

    def test_report_defaults_state_path_for_read_only_foods(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = self.write_ledger(directory)

            result = run_cli("--ledger", str(ledger_path), "foods", "--date", "2026-09-01")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Foods Eaten", result.stdout)
            self.assertIn("Eggs", result.stdout)

    def test_entry_template_outputs_valid_json_fields_payload_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = self.write_ledger(directory)

            result = run_cli("--ledger", str(ledger_path), "entry-template", "--meal", "breakfast", "--food-product", "Waterloo")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["meal_category"], "breakfast")
            self.assertEqual(payload["food_product"], "Waterloo")
            self.assertIn("calories", payload)
            self.assertIn("confidence_tier", payload)

    def test_food_master_find_summary_avoids_full_provenance_dump(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = self.write_ledger(directory)

            result = run_cli("--ledger", str(ledger_path), "food-master-find", "--query", "red plum", "--summary")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload[0]["food_master_id"], "FM-PLUM")
            self.assertIn("serving_weight_g", payload[0])
            self.assertNotIn("nutrient_provenance", payload[0])

    def test_add_from_master_accepts_amount_grams_without_manual_factor_math(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = self.write_ledger(directory)
            state_path = Path(directory) / "Fitness_Ledger_Nutrition_Current_State.json"

            result = run_cli(
                "--ledger", str(ledger_path),
                "--state", str(state_path),
                "add-from-master",
                "--date", "2026-09-01",
                "--date-source", "user_explicit",
                "--food-master-id", "FM-PLUM",
                "--meal", "breakfast",
                "--amount", "80 g red plum",
                "--amount-grams", "80",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            entry = ledger["entries"][-1]
            self.assertEqual(entry["amount_weight"], "80 g red plum")
            self.assertAlmostEqual(entry["calories"], 36.8, places=1)
            self.assertTrue(state_path.exists())

    def test_setup_import_promotes_import_archive_to_canonical_names(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "package"
            source.mkdir()
            (source / "IMPORT_Nutrition_Ledger.json").write_text(json.dumps(self.ledger()), encoding="utf-8")
            (source / "IMPORT_Nutrition_Current_State.json").write_text(
                json.dumps({"current_date": "2026-09-01"}),
                encoding="utf-8",
            )
            ledger_path = Path(directory) / "Fitness_Ledger_Nutrition_Ledger.json"

            result = run_cli("--ledger", str(ledger_path), "setup-import", "--source-dir", str(source))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(ledger_path.exists())
            self.assertTrue((Path(directory) / "Fitness_Ledger_Nutrition_Current_State.json").exists())
            payload = json.loads(result.stdout)
            self.assertEqual(payload["timezone"], "America/New_York")
            self.assertEqual(payload["state_current_date"], "2026-09-01")


if __name__ == "__main__":
    unittest.main()
