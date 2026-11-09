import json
import unittest
from pathlib import Path

# Configuration
ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "data" / "case_inputs.json"


class SnapshotTests(unittest.TestCase):
    def test_sources_and_missing_values_are_explicit(self):
        case = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        self.assertEqual(case["petition_date"], "2023-01-17")
        self.assertIsNone(case["liquidation"]["net_proceeds_mm"])
        self.assertEqual(len(case["capital_structure"]), 7)
        for record in case["verified_figures"]:
            self.assertTrue(record["source_id"])
            self.assertTrue(record["section"])
            self.assertEqual(record["status"], "verified")
