from __future__ import annotations

import math
import unittest

from prediction_engine import (
    InputValidationError,
    cesd_burden,
    load_bundle,
    predict_from_user_inputs,
    predict_probability,
)


class PredictionEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle()
        cls.example = cls.bundle["illustrative_profile"]

    def test_bundle_contract(self):
        self.assertEqual(len(self.bundle["models"]), 20)
        self.assertEqual(len(self.bundle["feature_order"]), 17)
        self.assertEqual(self.bundle["binary_order"], ["Sex", "Pain", "Internet use"])
        self.assertTrue(self.bundle["verification"]["passed"])

    def test_cesd_conversion(self):
        self.assertEqual(cesd_burden("CES-D-10", 9), 1.0)
        self.assertEqual(cesd_burden("CES-D-8", 2), 1.0)
        self.assertEqual(cesd_burden("CES-D-8", 1), 0.5)
        with self.assertRaises(InputValidationError):
            cesd_burden("CES-D-10", 10)
        with self.assertRaises(InputValidationError):
            cesd_burden("CES-D-8", 3)

    def test_reference_probability(self):
        actual = predict_probability(self.example["model_values"], bundle=self.bundle)
        expected = float(self.example["expected_probability"])
        self.assertTrue(math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12))

    def test_user_input_route(self):
        other = dict(self.example["model_values"])
        other.pop("Baseline subthreshold CES-D burden")
        actual = predict_from_user_inputs(
            self.example["cesd_instrument"],
            int(self.example["cesd_score"]),
            other,
            bundle=self.bundle,
        )
        self.assertTrue(0.0 <= actual <= 1.0)
        self.assertAlmostEqual(actual, float(self.example["expected_probability"]), places=12)

    def test_rejects_out_of_range_predictor(self):
        values = dict(self.example["model_values"])
        values["Mobility difficulty count"] = 7
        with self.assertRaises(InputValidationError):
            predict_probability(values, bundle=self.bundle)


if __name__ == "__main__":
    unittest.main()
