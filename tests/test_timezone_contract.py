import datetime as dt
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import unittest


SCRIPT = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts" / "nutrition_tracker.py"
LEDGER_FIXTURE = Path(__file__).parents[1] / "examples" / "sample_ledger.json"
SPEC = importlib.util.spec_from_file_location("nutrition_tracker_under_test", SCRIPT)
tracker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tracker)


class TimezoneContractTests(unittest.TestCase):
    def test_init_emits_complete_combined_sync_automation_contract(self):
        ledger = tracker.initialize_ledger(
            "America/New_York", sync_time="23:55", sources=["apple-health", "caliber"]
        )

        automation = ledger["sync"]["automation"]
        self.assertEqual(automation["title"], "Fitness Ledger Daily Sync")
        self.assertEqual(automation["timing_mode"], "exact_schedule")
        self.assertEqual(automation["default_timezone"], "America/New_York")
        self.assertEqual(automation["sync_time_local"], "23:55")
        self.assertIn("RRULE:FREQ=DAILY", automation["schedule"])
        self.assertIn("Apple Health", automation["prompt"])
        self.assertIn("Caliber", automation["prompt"])

    def test_automation_contract_uses_persisted_timezone_and_time(self):
        ledger = tracker.initialize_ledger("Asia/Tokyo", sync_time="00:10")

        automation = tracker.scheduled_sync_task_config(ledger)
        self.assertEqual(automation["default_timezone"], "Asia/Tokyo")
        self.assertEqual(automation["sync_time_local"], "00:10")

    def test_init_defaults_daily_combined_sync_to_near_midnight_local_time(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ledger.json"
            state_path = Path(directory) / "state.json"

            result = subprocess.run(
                [
                    sys.executable, str(SCRIPT), "--ledger", str(ledger_path), "--state", str(state_path),
                    "init", "--timezone", "America/New_York",
                ],
                capture_output=True, text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(ledger["sync"]["daily_sync_time_local"], "23:55")
            self.assertTrue(ledger["sync"]["daily_sync_enabled"])
            self.assertIsNone(ledger["sync"]["last_combined_sync_at"])

    def test_init_persists_custom_local_sync_time(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ledger.json"
            state_path = Path(directory) / "state.json"

            result = subprocess.run(
                [
                    sys.executable, str(SCRIPT), "--ledger", str(ledger_path), "--state", str(state_path),
                    "init", "--timezone", "Asia/Tokyo", "--sync-time", "00:10",
                ],
                capture_output=True, text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(ledger["sync"]["daily_sync_time_local"], "00:10")

    def test_sync_time_must_be_zero_padded_local_24_hour_time(self):
        for value in (" midnight", "24:00", "12:60", "9:05"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "HH:MM"):
                    tracker.validate_sync_time(value)

    def test_init_creates_configured_ledger_and_state(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ledger.json"
            state_path = Path(directory) / "state.json"

            result = subprocess.run(
                [
                    sys.executable, str(SCRIPT), "--ledger", str(ledger_path), "--state", str(state_path),
                    "init", "--timezone", "Asia/Tokyo", "--daily-calories", "2100",
                    "--daily-protein-g", "140", "--source", "apple-health", "--source", "caliber",
                ],
                capture_output=True, text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(ledger["timezone"], "Asia/Tokyo")
            self.assertEqual(ledger["targets"], {"daily_calories": 2100.0, "daily_protein_g": 140.0})
            self.assertEqual(ledger["source_adapters"]["apple-health"]["status"], "configured")
            self.assertEqual(ledger["source_adapters"]["caliber"]["status"], "configured")
            self.assertTrue(state_path.is_file())

    def test_init_refuses_to_overwrite_an_existing_ledger_without_force(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ledger.json"
            state_path = Path(directory) / "state.json"
            ledger_path.write_text('{"timezone": "Europe/London"}\n', encoding="utf-8")
            before = ledger_path.read_bytes()

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--ledger", str(ledger_path), "--state", str(state_path), "init", "--timezone", "Asia/Tokyo"],
                capture_output=True, text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already exists", result.stderr)
            self.assertEqual(ledger_path.read_bytes(), before)

    def test_timezone_is_required_and_never_defaults_to_a_region(self):
        with self.assertRaisesRegex(ValueError, "timezone is required"):
            tracker.timezone_for({})

        with self.assertRaisesRegex(ValueError, "timezone is required"):
            tracker.render_daily_report({"entries": [], "weights": []}, "2026-08-30")

    def test_timezone_must_be_a_valid_iana_identifier(self):
        with self.assertRaisesRegex(ValueError, "valid IANA timezone"):
            tracker.timezone_for({"timezone": "Eastern Time"})

    def test_any_configured_iana_timezone_drives_today(self):
        ledger = {"timezone": "Pacific/Auckland"}
        utc_now = dt.datetime(2026, 8, 30, 11, 30, tzinfo=dt.timezone.utc)

        self.assertEqual(tracker.current_local_date(ledger, now=utc_now), "2026-08-30")

    def test_today_uses_ledger_timezone_not_utc_date(self):
        ledger = {"timezone": "America/New_York"}
        utc_now = dt.datetime(2026, 8, 30, 0, 30, tzinfo=dt.timezone.utc)

        self.assertEqual(tracker.current_local_date(ledger, now=utc_now), "2026-08-29")

    def test_today_changes_at_new_york_midnight(self):
        ledger = {"timezone": "America/New_York"}
        utc_now = dt.datetime(2026, 8, 30, 4, 1, tzinfo=dt.timezone.utc)

        self.assertEqual(tracker.current_local_date(ledger, now=utc_now), "2026-08-30")

    def test_inferred_date_mismatch_is_rejected_instead_of_silently_logged(self):
        ledger = {"timezone": "America/New_York"}
        utc_now = dt.datetime(2026, 8, 30, 0, 30, tzinfo=dt.timezone.utc)

        with self.assertRaisesRegex(ValueError, "America/New_York"):
            tracker.resolve_entry_date(
                ledger,
                requested_date="2026-08-30",
                date_source="inferred",
                now=utc_now,
            )

    def test_user_explicit_date_can_override_current_new_york_date(self):
        ledger = {"timezone": "America/New_York"}
        utc_now = dt.datetime(2026, 8, 30, 0, 30, tzinfo=dt.timezone.utc)

        self.assertEqual(
            tracker.resolve_entry_date(
                ledger,
                requested_date="2026-08-30",
                date_source="user_explicit",
                now=utc_now,
            ),
            "2026-08-30",
        )

    def test_today_does_not_use_latest_future_entry_as_current_date(self):
        ledger = {
            "timezone": "America/New_York",
            "entries": [
                {"date": "2026-08-31", "deleted_at": None},
            ],
        }
        utc_now = dt.datetime(2026, 8, 30, 0, 30, tzinfo=dt.timezone.utc)

        self.assertEqual(tracker.current_local_date(ledger, now=utc_now), "2026-08-29")

    def test_daylight_saving_transition_uses_wall_clock_date(self):
        ledger = {"timezone": "America/New_York"}
        utc_now = dt.datetime(2026, 11, 1, 5, 30, tzinfo=dt.timezone.utc)

        self.assertEqual(tracker.current_local_date(ledger, now=utc_now), "2026-11-01")

    def test_missing_date_defaults_to_ledger_local_today(self):
        ledger = {"timezone": "America/New_York"}
        utc_now = dt.datetime(2026, 8, 30, 0, 30, tzinfo=dt.timezone.utc)

        self.assertEqual(
            tracker.resolve_entry_date(ledger, now=utc_now),
            "2026-08-29",
        )

    def test_cli_records_inferred_date_source_when_date_is_omitted(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ledger.json"
            state_path = Path(directory) / "state.json"
            shutil.copy(LEDGER_FIXTURE, ledger_path)
            state_path.write_text("{}\n", encoding="utf-8")
            fields = json.dumps({"meal_category": "snack", "food_product": "test item", "calories": 1, "confidence_tier": "C", "is_estimate": True})

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--ledger", str(ledger_path), "--state", str(state_path), "add", "--fields", fields],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            entry = ledger["entries"][-1]
            self.assertEqual(entry["date"], tracker.current_local_date(ledger))
            self.assertEqual(entry["date_source"], "inferred")

    def test_cli_rejects_mismatched_inferred_date_before_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ledger.json"
            state_path = Path(directory) / "state.json"
            shutil.copy(LEDGER_FIXTURE, ledger_path)
            state_path.write_text("{}\n", encoding="utf-8")
            before = ledger_path.read_bytes()
            fields = json.dumps({"meal_category": "snack", "food_product": "test item", "calories": 1, "confidence_tier": "C", "is_estimate": True})

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--ledger", str(ledger_path), "--state", str(state_path), "add", "--date", "2099-01-01", "--fields", fields],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("date_source=user_explicit", result.stderr)
            self.assertEqual(ledger_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
