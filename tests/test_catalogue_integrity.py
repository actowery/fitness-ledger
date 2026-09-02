import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from catalogue_integrity import NUTRIENT_FIELDS, catalogue_issues


def complete_master(**overrides):
    master = {
        "food_master_id": "FM-test",
        "food_name": "Test food",
        "source_urls": ["https://example.com/source"],
        "source_url": "https://example.com/source",
        "nutrients": {field: None for field in NUTRIENT_FIELDS},
        "nutrient_provenance": {field: {"tier": "D"} for field in NUTRIENT_FIELDS},
    }
    master.update(overrides)
    return master


class CatalogueIntegrityTests(unittest.TestCase):
    def test_complete_master_has_no_issues(self):
        self.assertEqual(catalogue_issues([complete_master()]), [])

    def test_rejects_partial_or_malformed_urls(self):
        master = complete_master(source_urls=["https://fdc.nal.u", "SRC-0001"], source_url="https://fdc.nal.u")
        issues = catalogue_issues([master])
        self.assertTrue(any("source_urls[0]" in issue for issue in issues))
        self.assertTrue(any("source_urls[1]" in issue for issue in issues))

    def test_rejects_invalid_hostname_characters(self):
        issues = catalogue_issues([complete_master(source_urls=["https://example,com/source"])])
        self.assertTrue(any("source_urls[0]" in issue for issue in issues))

    def test_reports_non_mapping_master_instead_of_crashing(self):
        issues = catalogue_issues([None])
        self.assertEqual(issues, ["unknown: food-master record must be an object"])

    def test_rejects_primary_url_mismatch(self):
        issues = catalogue_issues([complete_master(source_url="https://example.com/other")])
        self.assertTrue(any("source_url must equal source_urls[0]" in issue for issue in issues))

    def test_rejects_missing_nutrient_and_provenance_categories(self):
        master = complete_master()
        del master["nutrients"]["vitamin_k_mcg"]
        del master["nutrient_provenance"]["water_g"]
        issues = catalogue_issues([master])
        self.assertTrue(any("missing nutrient field vitamin_k_mcg" in issue for issue in issues))
        self.assertTrue(any("missing provenance field water_g" in issue for issue in issues))

    def test_current_local_catalogue_is_complete_when_present(self):
        path = Path(__file__).parents[1] / "Fitness_Ledger_Nutrition_Ledger.json"
        if not path.exists():
            self.skipTest("canonical personal ledger is gitignored and unavailable in clean checkouts")
        ledger = json.loads(path.read_text(encoding="utf-8"))
        masters = ledger.get("food_master", [])
        self.assertGreaterEqual(len(masters), 150)
        self.assertEqual(len({master.get("food_master_id") for master in masters}), len(masters))
        self.assertEqual(catalogue_issues(masters), [])


if __name__ == "__main__":
    unittest.main()
