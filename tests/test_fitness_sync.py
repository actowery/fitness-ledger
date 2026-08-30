import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "fitness-sync" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from combined_sync import run_combined_sync
from fitness_sync import reconcile_steps, sync_workouts, sync_fitness_sources, validate_workouts, validate_health_response


class FitnessSyncTests(unittest.TestCase):
    def test_empty_apple_workout_pull_is_a_successful_zero_result(self):
        result = sync_workouts(caliber_workouts=[], apple_health_workouts=[], existing=[])

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["apple_health_workouts"], 0)
        self.assertEqual(result["canonical"], [])

    def test_existing_identical_workout_is_unchanged_not_duplicated(self):
        workout = {
            "calendarItemId": "w-1", "date": "2026-08-25", "workoutTitle": "The B-Side",
            "status": "COMPLETED", "durationSeconds": 3600,
            "exercises": [{"exerciseId": "squat", "exerciseName": "Barbell Squat", "sortOrder": 0,
                           "sets": [{"sortOrder": 0, "actualWeight": 145, "actualReps": 5}]}],
        }
        result = sync_workouts([workout], [], existing=[workout])

        self.assertEqual(result["counts"], {"new": 0, "updated": 0, "unchanged": 1})
        self.assertEqual(len(result["canonical"]), 1)

    def test_changed_workout_is_updated_by_stable_workout_id(self):
        old = {
            "calendarItemId": "w-1", "date": "2026-08-25", "workoutTitle": "The B-Side",
            "status": "COMPLETED", "durationSeconds": 3600, "exercises": [],
        }
        new = {**old, "durationSeconds": 3660}
        result = sync_workouts([new], [], existing=[old])

        self.assertEqual(result["counts"], {"new": 0, "updated": 1, "unchanged": 0})
        self.assertEqual(result["canonical"][0]["durationSeconds"], 3660)

    def test_empty_apple_workout_pull_does_not_delete_caliber_workout(self):
        workout = {"calendarItemId": "w-1", "date": "2026-08-25", "workoutTitle": "The B-Side", "status": "COMPLETED", "exercises": []}
        result = sync_workouts([workout], [], existing=[])

        self.assertEqual(len(result["canonical"]), 1)
        self.assertTrue(result["apple_health_check"]["complete"])

    def test_apple_health_steps_outrank_stale_caliber_steps_without_addition(self):
        result = reconcile_steps(
            caliber_steps=[{"date": "2026-08-28", "steps": 8383}],
            apple_health_steps=[{"date": "2026-08-28", "steps": 18284, "complete": True}],
        )

        self.assertEqual(result["by_date"]["2026-08-28"]["steps"], 18284)
        self.assertEqual(result["by_date"]["2026-08-28"]["source"], "apple_health")
        self.assertEqual(result["by_date"]["2026-08-28"]["conflict"]["caliber"], 8383)

    def test_caliber_steps_are_never_canonical_when_apple_health_has_no_value(self):
        result = reconcile_steps(
            caliber_steps=[{"date": "2026-08-29", "steps": 9000}],
            apple_health_steps=[],
        )

        self.assertNotIn("2026-08-29", result["by_date"])
        self.assertEqual(result["ignored_sources"]["caliber"]["2026-08-29"], 9000)

    def test_combined_sync_emits_nontraining_days_and_source_checks(self):
        result = sync_fitness_sources(
            caliber_workouts=[], apple_health_workouts=[], existing_workouts=[],
            caliber_steps=[{"date": "2026-08-27", "steps": 338}],
            apple_health_steps=[{"date": "2026-08-27", "steps": 5000, "complete": True}],
            dates=["2026-08-27", "2026-08-28"],
        )

        self.assertEqual(result["daily"]["2026-08-28"]["training_day"], False)
        self.assertEqual(result["daily"]["2026-08-27"]["steps"], 5000)
        self.assertEqual(result["checks"]["apple_health_workouts"]["status"], "complete_zero")

    def test_combined_sync_runs_every_source_check_on_a_rest_day(self):
        calls = []

        def source(name, value):
            def fetch():
                calls.append(name)
                return value
            return fetch

        result = run_combined_sync(
            fetch_nutrition=source("nutrition", {"status": "complete"}),
            fetch_caliber_workouts=source("caliber_workouts", []),
            fetch_apple_health_workouts=source("apple_health_workouts", []),
            fetch_apple_health_activity=source("apple_health_activity", {"steps": []}),
            existing_workouts=[], caliber_steps=[], dates=["2026-08-30"],
        )

        self.assertEqual(calls, ["nutrition", "caliber_workouts", "apple_health_workouts", "apple_health_activity"])
        self.assertEqual(result["source_runs"]["apple_health_workouts"], "complete_zero")
        self.assertFalse(result["daily"]["2026-08-30"]["training_day"])

    def test_workout_validation_rejects_duplicate_set_identity(self):
        workout = {
            "calendarItemId": "w-1", "date": "2026-08-25", "exercises": [
                {"exerciseId": "squat", "sets": [
                    {"sortOrder": 0, "actualWeight": 145, "actualReps": 5},
                    {"sortOrder": 0, "actualWeight": 145, "actualReps": 5},
                ]}
            ]
        }

        errors = validate_workouts([workout], as_of="2026-08-30")

        self.assertTrue(any("duplicate set" in error for error in errors))

    def test_workout_validation_rejects_future_and_negative_values(self):
        workout = {
            "calendarItemId": "w-1", "date": "2026-09-01", "durationSeconds": -1,
            "exercises": [{"exerciseId": "squat", "sets": [{"sortOrder": 0, "actualWeight": -5, "actualReps": -1}]}],
        }

        errors = validate_workouts([workout], as_of="2026-08-30")

        self.assertTrue(any("future" in error for error in errors))
        self.assertTrue(any("negative" in error for error in errors))

    def test_workout_validation_requires_stable_id_and_date(self):
        errors = validate_workouts([{"exercises": []}], as_of="2026-08-30")

        self.assertTrue(any("stable workout ID" in error for error in errors))
        self.assertTrue(any("date" in error for error in errors))

    def test_health_response_incompleteness_is_blocking(self):
        response = {"result_status": {"metrics": {"stepCount": {"complete": False, "row_limit_exceeded": True}}}, "data": {}}

        errors = validate_health_response(response)

        self.assertTrue(any("incomplete" in error for error in errors))
        self.assertTrue(any("row limit" in error for error in errors))

    def test_health_response_rejects_future_activity_rows(self):
        response = {"result_status": {"metrics": {"stepCount": {"complete": True}}},
                    "data": {"stepCount": [{"time_local": "2026-09-01T00:00:00-04:00", "value": 10}]}}

        errors = validate_health_response(response, as_of="2026-08-30")

        self.assertTrue(any("future" in error for error in errors))

    def test_invalid_workout_payload_blocks_reconciliation(self):
        with self.assertRaises(ValueError):
            sync_workouts([{"calendarItemId": "w-1", "date": "2026-08-25", "durationSeconds": -1}], [], [])

    def test_incomplete_health_response_blocks_combined_fitness_sync(self):
        response = {
            "result_status": {"metrics": {"stepCount": {"complete": False}}},
            "data": {},
        }
        with self.assertRaises(ValueError):
            sync_fitness_sources(
                caliber_workouts=[], apple_health_workouts=[], existing_workouts=[],
                caliber_steps=[], apple_health_steps=[], dates=["2026-08-30"],
                apple_health_response=response, as_of="2026-08-30",
            )


if __name__ == "__main__":
    unittest.main()
