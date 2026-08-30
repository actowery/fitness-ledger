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
