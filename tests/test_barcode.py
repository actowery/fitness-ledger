import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from barcode import barcode_fast_path, verification_is_stale


class BarcodeFastPathTests(unittest.TestCase):
    NOW = datetime(2026, 8, 31, tzinfo=timezone.utc)

    def test_fresh_verified_barcode_reuses_local_master_without_external_lookup(self):
        master = {"gtin": "012345678901", "food_master_id": "fm-1", "last_verified_at": "2026-08-01T00:00:00Z"}
        result = barcode_fast_path("012345678901", [master], now=self.NOW)
        self.assertEqual(result["status"], "reused")

    def test_stale_barcode_revalidates_against_authoritative_candidate(self):
        local = {"gtin": "012345678901", "food_master_id": "fm-1", "last_verified_at": "2025-01-01T00:00:00Z"}
        authoritative = {"gtin": "012345678901", "source": "manufacturer", "source_id": "m-1", "calories": 160}
        result = barcode_fast_path("012345678901", [local], [authoritative], now=self.NOW)
        self.assertEqual(result["status"], "revalidated")
        self.assertEqual(result["selected"]["source_id"], "m-1")

    def test_stale_local_master_is_not_silently_presented_as_fresh_offline(self):
        local = {"gtin": "012345678901", "food_master_id": "fm-1", "last_verified_at": "2025-01-01T00:00:00Z"}
        result = barcode_fast_path("012345678901", [local], now=self.NOW)
        self.assertEqual(result["status"], "stale_local")

    def test_unknown_barcode_is_unresolved(self):
        result = barcode_fast_path("000000000000", [], now=self.NOW)
        self.assertEqual(result["status"], "unresolved")

    def test_duplicate_barcode_masters_are_ambiguous(self):
        masters = [{"gtin": "012345678901", "food_master_id": "fm-1"}, {"gtin": "012345678901", "food_master_id": "fm-2"}]
        result = barcode_fast_path("012345678901", masters, now=self.NOW)
        self.assertEqual(result["status"], "ambiguous")

    def test_invalid_or_missing_verification_timestamp_is_stale(self):
        self.assertTrue(verification_is_stale(None, now=self.NOW))
        self.assertTrue(verification_is_stale("not-a-date", now=self.NOW))


if __name__ == "__main__":
    unittest.main()
