import math
import unittest

from ch11.model import Claim, case_claims, case_waterfall, equity_bridge, thresholds, waterfall
from ch11.report import load_case, scenario_values, tables


class WaterfallTests(unittest.TestCase):
    def setUp(self):
        self.claims = [Claim("senior", 60, 1, "A"), Claim("junior1", 20, 2, "B"), Claim("junior2", 40, 2, "B")]

    def test_hand_computed_partial_pari_passu(self):
        result = waterfall(100, self.claims, senior_cost=10)
        self.assertEqual(result["payments"], {"senior": 60, "junior1": 10, "junior2": 20})
        self.assertEqual(result["fulcrum"], ["junior1", "junior2"])
        self.assertEqual(result["equity"], 0)

    def test_hand_computed_senior_shortfall(self):
        result = waterfall(5, self.claims, senior_cost=10)
        self.assertEqual(result["senior_paid"], 5)
        self.assertEqual(result["senior_shortfall"], 5)
        self.assertTrue(all(value == 0 for value in result["payments"].values()))

    def test_equity_and_cash(self):
        result = waterfall(140, self.claims, cash=5, senior_cost=10)
        self.assertEqual(result["equity"], 15)
        self.assertEqual(result["fulcrum"], [])

    def test_hand_computed_thresholds_and_boundaries(self):
        result = thresholds(self.claims, cash=5, senior_cost=10)
        self.assertEqual(result["senior"], {"attachment_ev": 5, "full_recovery_ev": 65})
        self.assertEqual(result["junior2"], {"attachment_ev": 65, "full_recovery_ev": 125})
        self.assertEqual(waterfall(65, self.claims, cash=5, senior_cost=10)["recoveries"]["senior"], 1)
        self.assertEqual(waterfall(65, self.claims, cash=5, senior_cost=10)["recoveries"]["junior1"], 0)

    def test_order_independence(self):
        self.assertEqual(waterfall(100, self.claims)["payments"], waterfall(100, self.claims[::-1])["payments"])

    def test_zero_claim_and_empty_stack(self):
        result = waterfall(10, [Claim("zero", 0, 1, "A")])
        self.assertIsNone(result["recoveries"]["zero"])
        self.assertEqual(result["equity"], 10)
        self.assertEqual(waterfall(10, [])["equity"], 10)

    def test_invalid_inputs(self):
        for ev in (-1, math.nan, math.inf, True, "100"):
            with self.assertRaises(ValueError):
                waterfall(ev, self.claims)
        for claims in ([Claim("x", -1, 1, "A")], [Claim("x", 1, 0, "A")],
                       [Claim("x", 1, 1, "A"), Claim("x", 2, 2, "B")]):
            with self.assertRaises(ValueError):
                waterfall(100, claims)

    def test_equity_bridge_floor(self):
        self.assertEqual(equity_bridge(90, 100), {"signed_equity": -10, "equity": 0})

    def test_conservation_and_monotonicity(self):
        previous = dict.fromkeys((claim.identifier for claim in self.claims), 0)
        for ev in range(201):
            result = waterfall(ev, self.claims, senior_cost=10)
            self.assertAlmostEqual(result["senior_paid"] + sum(result["payments"].values()) + result["equity"], ev)
            for identifier, value in result["payments"].items():
                self.assertGreaterEqual(value + 1e-12, previous[identifier])
            previous = result["payments"]


class CaseTests(unittest.TestCase):
    def test_case_exact_boundaries_have_no_ghost_fulcrum(self):
        case = load_case()
        for boundary in thresholds(case_claims(case), senior_cost=150).values():
            result = case_waterfall(case, boundary["full_recovery_ev"])
            self.assertEqual(result["fulcrum"], [])

    def test_base_against_hand_calculation(self):
        case = load_case()
        result = case_waterfall(case, 612.5)
        secured_cash = 612.5 - 150 - 407.282561 - 17.1105
        self.assertAlmostEqual(secured_cash, 38.106939)
        self.assertAlmostEqual(result["recoveries"]["secured_fixed"], 38.106939 / 911.7)
        self.assertEqual(result["recoveries"]["unsecured_2026"], 0)
        self.assertAlmostEqual(sum(claim.amount for claim in case_claims(case)), 1451.293061)

    def test_range_and_vintages(self):
        case = load_case()
        self.assertEqual(scenario_values(case), {"low": 450, "base": 612.5, "high": 775})
        output = tables(case)
        self.assertTrue(all(row["filed_liquidation_recovery"] is None for row in output["liquidation_comparison"]))
        self.assertEqual(len(output["sensitivity"]), 96)
        base_bridge = next(row for row in output["valuation_bridge"] if row["scenario"] == "base")
        self.assertEqual(base_bridge["equity"], 99.5)
