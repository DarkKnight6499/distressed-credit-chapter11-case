import copy
import unittest
from pathlib import Path

from openpyxl import Workbook, load_workbook

from ch11.excel_eval import FormulaEvaluator
from ch11.model import case_claims, case_waterfall, thresholds
from ch11.report import load_case, tables

# Configuration
ROOT = Path(__file__).resolve().parents[2]
WORKBOOK_PATH = ROOT / "excel/chapter11.xlsx"
TOLERANCE = 1e-8
FIRST_WATERFALL_ROW = 11
SCENARIO_ROWS = {"low": 34, "base": 35, "high": 36}
CLASS_COLUMNS = {"3A": 5, "3B": 6, "4": 7, "5": 8}


class EvaluatorTests(unittest.TestCase):
    def test_hand_computed_functions_and_lazy_if(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet["A1"], sheet["A2"], sheet["A3"] = 1, 2, 3
        sheet["B1"], sheet["B2"], sheet["B3"] = 10, 20, 40
        sheet["C1"] = '=SUMIF(A1:A3,"<"&3,B1:B3)'
        sheet["C2"] = '=IF(A1=1,MAX(0,100-SUM(B1:B3)),1/0)'
        sheet["C3"] = "=MIN(100,ABS(-5)*2)+10/2"
        evaluator = FormulaEvaluator(workbook)
        self.assertEqual(evaluator.cell(sheet.title, "C1"), 30)
        self.assertEqual(evaluator.cell(sheet.title, "C2"), 30)
        self.assertEqual(evaluator.cell(sheet.title, "C3"), 15)

    def test_reject_cycle_and_unsupported_code(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet["A1"] = "=A1+1"
        with self.assertRaises(ValueError):
            FormulaEvaluator(workbook).cell(sheet.title, "A1")
        sheet["A1"] = "=HYPERLINK(1)"
        with self.assertRaises(ValueError):
            FormulaEvaluator(workbook).cell(sheet.title, "A1")


class ExcelReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.case = load_case()
        self.workbook = load_workbook(WORKBOOK_PATH)
        self.evaluator = FormulaEvaluator(self.workbook)

    def tearDown(self):
        self.workbook.close()

    def assert_close(self, actual, expected):
        self.assertIsInstance(actual, (int, float))
        self.assertLessEqual(abs(actual - expected), TOLERANCE)

    def test_active_waterfall_and_thresholds(self):
        result = case_waterfall(self.case, self.workbook["Inputs"]["B4"].value)
        claim_thresholds = thresholds(case_claims(self.case), senior_cost=150)
        for row, claim in enumerate(case_claims(self.case), FIRST_WATERFALL_ROW):
            self.assert_close(self.evaluator.cell("Waterfall", f"F{row}"), result["payments"][claim.identifier])
            self.assert_close(self.evaluator.cell("Waterfall", f"G{row}"), result["recoveries"][claim.identifier])
            self.assert_close(self.evaluator.cell("Waterfall", f"B{row + 14}"), claim_thresholds[claim.identifier]["attachment_ev"])
            self.assert_close(self.evaluator.cell("Waterfall", f"C{row + 14}"), claim_thresholds[claim.identifier]["full_recovery_ev"])
        self.assert_close(self.evaluator.cell("Waterfall", "B19"), result["equity"])
        self.assert_close(self.evaluator.cell("Waterfall", "B20"), 0)
        self.assertEqual(self.evaluator.cell("Waterfall", "B21"), "4")

    def test_all_scenarios_and_sensitivity(self):
        output = tables(self.case)
        for record in output["class_recoveries"]:
            row = SCENARIO_ROWS[record["scenario"]]
            column = CLASS_COLUMNS[record["class"]]
            self.assert_close(self.evaluator.cell("Waterfall", self.workbook["Waterfall"].cell(row, column).coordinate), record["recovery"])
        for record in output["valuation_bridge"]:
            row = SCENARIO_ROWS[record["scenario"]]
            self.assert_close(self.evaluator.cell("Waterfall", f"C{row}"), record["signed_equity"])
            self.assert_close(self.evaluator.cell("Waterfall", f"D{row}"), record["equity"])
        sensitivity = {(record["ebitda_factor"], record["multiple"], record["class"]): record for record in output["sensitivity"]}
        for row in range(5, 29):
            factor = self.workbook["Sensitivity"].cell(row, 1).value
            multiple = self.workbook["Sensitivity"].cell(row, 2).value
            for plan_class, column in CLASS_COLUMNS.items():
                reference = self.workbook["Sensitivity"].cell(row, column).coordinate
                self.assert_close(self.evaluator.cell("Sensitivity", reference), sensitivity[(factor, multiple, plan_class)]["recovery"])

    def test_input_changes_recalculate(self):
        for ev, dip, cash, admin in ((0, 150, 0, 0), (150, 150, 0, 0), (450, 150, 0, 0),
                                     (612.5, 150, 0, 0), (775, 150, 0, 0), (2000, 100, 25, 50),
                                     (500, 150, -25, 30)):
            modified = copy.deepcopy(self.case)
            modified["assumptions"].update(dip_proxy_mm=dip, cash_adjustment_mm=cash, administrative_reserve_mm=admin)
            for coordinate, value in (("B4", ev), ("B5", dip), ("B6", cash), ("B7", admin)):
                self.workbook["Inputs"][coordinate] = value
            evaluator = FormulaEvaluator(self.workbook)
            expected = case_waterfall(modified, ev)
            for row, claim in enumerate(case_claims(modified), FIRST_WATERFALL_ROW):
                self.assert_close(evaluator.cell("Waterfall", f"F{row}"), expected["payments"][claim.identifier])
            self.assert_close(evaluator.cell("Waterfall", "B19"), expected["equity"])
            self.assert_close(evaluator.cell("Waterfall", "B20"), 0)

    def test_claim_and_ebitda_changes_recalculate(self):
        modified = copy.deepcopy(self.case)
        modified["capital_structure"][4]["model_claim_mm"] = 600
        self.workbook["Inputs"]["E18"] = 600
        self.workbook["Inputs"]["B8"] = 100
        evaluator = FormulaEvaluator(self.workbook)
        expected = case_waterfall(modified, 612.5)
        self.assert_close(evaluator.cell("Waterfall", "F14"), expected["payments"]["secured_fixed"])
        self.assert_close(evaluator.cell("Sensitivity", "D5"), 150)
        self.assert_close(evaluator.cell("Sensitivity", "E5"), 0)

    def test_zero_claim_and_exact_boundary_classification(self):
        self.workbook["Inputs"]["E17"] = 0
        evaluator = FormulaEvaluator(self.workbook)
        self.assertEqual(evaluator.cell("Waterfall", "G13"), "N/A")
        self.assertEqual(evaluator.cell("Waterfall", "J13"), "N/A")
        self.assertEqual(evaluator.cell("Waterfall", "B21"), "4")
        self.workbook["Inputs"]["E17"] = 161.7
        self.workbook["Inputs"]["B4"] = 574.393061
        evaluator = FormulaEvaluator(self.workbook)
        self.assertEqual(evaluator.cell("Waterfall", "B21"), "No partially paid class")

    def test_caches_match_evaluated_live_formulas(self):
        cached = load_workbook(WORKBOOK_PATH, data_only=True)
        try:
            for (sheet, coordinate), expected in self.evaluator.all_formulas().items():
                actual = cached[sheet][coordinate].value
                if isinstance(expected, str):
                    self.assertEqual(actual, expected)
                else:
                    self.assert_close(actual, expected)
        finally:
            cached.close()

    def test_plain_formatting_and_author(self):
        self.assertEqual(self.workbook.properties.creator, "Yazad Madan")
        for sheet in self.workbook:
            self.assertIsNone(sheet.sheet_properties.tabColor)
            for row in sheet:
                for cell in row:
                    self.assertIsNone(cell.fill.patternType)
                    if cell.value is not None:
                        self.assertIsNone(cell.font.color)
