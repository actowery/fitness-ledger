import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from confidence import confidence_dimensions, explain_confidence


class ConfidenceTests(unittest.TestCase):
    def test_weighed_generic_produce_separates_identity_portion_and_composition(self):
        result = confidence_dimensions({
            "food_product": "peach", "amount_weight": "80 g",
            "nutrient_provenance": {"calories": {"tier": "B"}, "vitamin_e_mg": {"tier": "B"}},
        })
        self.assertEqual(result, {"identity_confidence": "moderate", "portion_confidence": "high", "composition_confidence": "high"})

    def test_exact_packaged_label_is_high_across_dimensions(self):
        result = confidence_dimensions({
            "gtin": "012345678901", "food_master_id": "fm-1", "amount_weight": "414 g",
            "nutrient_provenance": {"calories": {"tier": "A"}, "protein_g": {"tier": "A"}},
        })
        self.assertEqual(result, {"identity_confidence": "high", "portion_confidence": "high", "composition_confidence": "high"})

    def test_restaurant_estimate_can_have_low_composition_despite_known_portion(self):
        result = confidence_dimensions({
            "food_product": "restaurant entree", "serving_count": 1,
            "nutrient_provenance": {"calories": {"tier": "C"}, "magnesium_mg": {"tier": "D"}},
        })
        self.assertEqual(result["portion_confidence"], "high")
        self.assertEqual(result["composition_confidence"], "moderate")

    def test_ambiguous_branded_variant_is_low_identity(self):
        result = confidence_dimensions({
            "food_product": "Fairlife chocolate", "identity_status": "ambiguous",
            "nutrient_provenance": {"calories": {"tier": "A"}},
        })
        self.assertEqual(result["identity_confidence"], "low")

    def test_explanation_is_human_readable_without_opaque_composite_score(self):
        explanation = explain_confidence({"food_master_id": "fm-1", "amount_weight": "10 g", "nutrient_provenance": {"calories": {"tier": "A"}}})
        self.assertIn("identity: high", explanation)
        self.assertIn("portion: high", explanation)
        self.assertIn("composition: high", explanation)
        self.assertNotIn("score", explanation.lower())


if __name__ == "__main__":
    unittest.main()
