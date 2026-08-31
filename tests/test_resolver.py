import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from resolver import resolve_candidates


class ResolverTests(unittest.TestCase):
    def test_exact_barcode_prefers_manufacturer_over_open_food_facts(self):
        result = resolve_candidates({"gtin": "012345678901"}, [
            {"gtin": "012345678901", "source": "open_food_facts", "source_id": "off-1"},
            {"gtin": "012345678901", "source": "manufacturer", "source_id": "m-1"},
        ])
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["source"], "manufacturer")

    def test_exact_name_requires_full_identity_match(self):
        result = resolve_candidates(
            {"brand_owner": "A", "product_name": "Shake", "variant": "Chocolate", "package_size": "14 oz"},
            [{"brand_owner": "A", "product_name": "Shake", "variant": "Chocolate", "package_size": "11 oz", "source": "manufacturer"}],
        )
        self.assertEqual(result["status"], "unresolved")

    def test_conflicting_same_priority_candidates_remain_ambiguous(self):
        result = resolve_candidates({"gtin": "012345678901"}, [
            {"gtin": "012345678901", "source": "manufacturer", "source_id": "m-1"},
            {"gtin": "012345678901", "source": "manufacturer", "source_id": "m-2"},
        ])
        self.assertEqual(result["status"], "ambiguous")

    def test_unavailable_sources_leave_query_unresolved(self):
        result = resolve_candidates({"product_name": "Unknown"}, [])
        self.assertEqual(result["status"], "unresolved")
        self.assertIsNone(result["selected"])

    def test_analogue_is_lower_priority_than_verified_local(self):
        result = resolve_candidates({"gtin": "012345678901"}, [
            {"gtin": "012345678901", "source": "usda_analogue", "source_id": "u-1"},
            {"gtin": "012345678901", "source": "verified_local", "source_id": "local-1"},
        ])
        self.assertEqual(result["source"], "verified_local")

    def test_gtin_miss_does_not_fall_back_to_unrelated_name(self):
        result = resolve_candidates({"gtin": "099999999999", "product_name": "Shake"}, [{"gtin": "012345678901", "product_name": "Shake", "source": "manufacturer"}])
        self.assertEqual(result["status"], "unresolved")


if __name__ == "__main__":
    unittest.main()
