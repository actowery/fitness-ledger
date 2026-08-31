import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from product_identity import formulation_fingerprint, resolve_identity, version_master


class ProductIdentityTests(unittest.TestCase):
    def setUp(self):
        self.shake = {
            "food_master_id": "fm-shake-v1",
            "gtin": "081234567890",
            "brand_owner": "Example Nutrition",
            "manufacturer": "Example Nutrition",
            "product_name": "Chocolate Protein Shake",
            "variant": "chocolate",
            "package_size": "14 fl oz",
            "serving_size": 1,
            "serving_unit": "bottle",
            "serving_weight_g": 414,
            "calories": 150,
            "protein_g": 30,
            "carbohydrates_g": 5,
            "fat_g": 3,
            "sodium_mg": 240,
        }

    def test_formulation_fingerprint_is_deterministic_and_normalized(self):
        altered_formatting = {**self.shake, "product_name": "  CHOCOLATE   PROTEIN SHAKE "}
        self.assertEqual(formulation_fingerprint(self.shake), formulation_fingerprint(altered_formatting))

    def test_exact_gtin_match(self):
        result = resolve_identity({"gtin": "081234567890"}, [self.shake])
        self.assertEqual(result.status, "exact")
        self.assertEqual(result.selected["food_master_id"], "fm-shake-v1")

    def test_same_name_different_package_does_not_match(self):
        other = {**self.shake, "gtin": "081234567891", "package_size": "11 fl oz"}
        result = resolve_identity({"product_name": self.shake["product_name"], "variant": "chocolate", "package_size": "14 fl oz"}, [other])
        self.assertEqual(result.status, "unresolved")

    def test_same_brand_similar_variant_is_unresolved_without_barcode(self):
        other = {**self.shake, "gtin": None, "variant": "vanilla"}
        result = resolve_identity({"brand_owner": "Example Nutrition", "product_name": "Protein Shake"}, [self.shake, other])
        self.assertIn(result.status, {"ambiguous", "unresolved"})

    def test_changed_formulation_same_gtin_requires_new_version(self):
        observed = {**self.shake, "calories": 160, "protein_g": 32}
        result = resolve_identity({"gtin": self.shake["gtin"], "formulation_hash": formulation_fingerprint(observed)}, [self.shake])
        self.assertEqual(result.status, "changed_formulation")
        new = version_master(self.shake, observed)
        self.assertEqual(new["supersedes_food_master_id"], "fm-shake-v1")
        self.assertEqual(new["food_master_version"], 2)
        self.assertNotEqual(new["food_master_id"], new["supersedes_food_master_id"])
        self.assertNotEqual(new["formulation_hash"], formulation_fingerprint(self.shake))

    def test_duplicate_masters_with_same_gtin_are_ambiguous(self):
        duplicate = {**self.shake, "food_master_id": "fm-duplicate"}
        result = resolve_identity({"gtin": self.shake["gtin"]}, [self.shake, duplicate])
        self.assertEqual(result.status, "ambiguous")

    def test_name_only_query_does_not_get_tier_a_exact_identity(self):
        result = resolve_identity({"product_name": "Chocolate Protein Shake"}, [self.shake])
        self.assertNotEqual(result.status, "exact")

    def test_name_identity_can_match_master_that_has_gtin(self):
        result = resolve_identity({"brand_owner": "Example Nutrition", "manufacturer": "Example Nutrition", "product_name": "Chocolate Protein Shake", "variant": "chocolate", "package_size": "14 fl oz"}, [self.shake])
        self.assertEqual(result.status, "exact")

    def test_same_formulation_reuses_existing_version(self):
        result = version_master(self.shake, dict(self.shake))
        self.assertEqual(result["food_master_id"], "fm-shake-v1")
        self.assertNotIn("supersedes_food_master_id", result)


if __name__ == "__main__":
    unittest.main()
