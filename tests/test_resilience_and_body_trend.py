import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from body_trend import smoothed_weights
from resilience import resolve_with_fallback


class ResilienceAndBodyTrendTests(unittest.TestCase):
    def test_external_failure_uses_existing_master_without_inventing_fresh_verification(self):
        master = {"food_master_id": "fm-1", "calories": 100}
        result = resolve_with_fallback(master, {"status": "error"})
        self.assertEqual(result["status"], "local_fallback")
        self.assertEqual(result["verification"], "age-limited")

    def test_no_local_or_external_source_is_unresolved(self):
        result = resolve_with_fallback(None, {"status": "error"})
        self.assertEqual(result["status"], "unresolved")

    def test_weight_trend_is_smoothed_and_reports_sample_size(self):
        result = smoothed_weights([{"date": "2026-08-01", "weight_lb": 216}, {"date": "2026-08-02", "weight_lb": 214}], window=2)
        self.assertEqual(result[-1]["smoothed_weight_lb"], 215.0)
        self.assertEqual(result[-1]["sample_size"], 2)


if __name__ == "__main__": unittest.main()
