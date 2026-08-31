import copy
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from migration import enrich_food_masters, migrate_ledger_v2


class MigrationTests(unittest.TestCase):
    def test_migration_preserves_entry_identity_values_and_tombstones(self):
        ledger = {"schema_version": "1.0.0", "entries": [{"entry_id": "e1", "food_product": "Peach", "calories": 50, "revision": 3, "deleted_at": "2026-08-30T00:00:00Z"}]}
        result = migrate_ledger_v2(ledger)
        self.assertEqual(result["entries"][0]["entry_id"], "e1")
        self.assertEqual(result["entries"][0]["calories"], 50)
        self.assertEqual(result["entries"][0]["revision"], 3)
        self.assertEqual(result["entries"][0]["deleted_at"], ledger["entries"][0]["deleted_at"])
        self.assertEqual(result["schema_version"], "2.0.0")

    def test_migration_is_idempotent(self):
        ledger = {"schema_version": "1.0.0", "entries": [{"entry_id": "e1", "food_product": "Peach"}]}
        once = migrate_ledger_v2(ledger)
        twice = migrate_ledger_v2(once)
        self.assertEqual(once, twice)

    def test_migration_does_not_mutate_input(self):
        ledger = {"schema_version": "1.0.0", "entries": [{"entry_id": "e1", "food_product": "Peach"}]}
        before = copy.deepcopy(ledger)
        migrate_ledger_v2(ledger)
        self.assertEqual(ledger, before)

    def test_food_master_enrichment_fills_only_derivable_identity_metadata(self):
        ledger = {"food_master": [{"food_master_id": "fm-1", "food_name": "Peach", "brand": None, "date_last_verified": "2026-08-30", "nutrients": {"calories": 50}}], "entries": [{"food_master_id": "fm-1", "created_at": "2026-08-30T12:00:00-04:00"}]}
        result = enrich_food_masters(ledger)
        master = result["food_master"][0]
        self.assertEqual(master["product_name"], "Peach")
        self.assertEqual(master["first_seen_at"], "2026-08-30T12:00:00-04:00")
        self.assertTrue(master["formulation_hash"])
        self.assertIsNone(master["manufacturer"])
        self.assertEqual(result["schema_version"], "2.1.0")

    def test_food_master_enrichment_is_idempotent(self):
        ledger = {"schema_version": "2.0.0", "food_master": [{"food_master_id": "fm-1", "food_name": "Peach", "nutrients": {"calories": 50}}], "entries": []}
        once = enrich_food_masters(ledger)
        self.assertEqual(once, enrich_food_masters(once))


if __name__ == "__main__": unittest.main()
