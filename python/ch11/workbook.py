"""Build the Excel model. Native Excel recalculation is a separate local step."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties

from .report import load_case, scenario_values

# Configuration
ROOT = Path(__file__).resolve().parents[2]
WORKBOOK_PATH = ROOT / "excel/chapter11.xlsx"
AUTHOR = "Yazad Madan"
FONT_NAME = "Arial"
BODY_SIZE = 10
MONEY_FORMAT = '#,##0.000;(#,##0.000);0.000'
PERCENT_FORMAT = "0.00%"
FIRST_CLAIM_ROW = 15
FIRST_WATERFALL_ROW = 11
INPUT_CELLS = {"ev": "B4", "dip": "B5", "cash": "B6", "admin": "B7", "ebitda": "B8", "net_debt": "B9", "low": "B10", "high": "B11", "tolerance": "B12"}


def _header(sheet, row, labels):
    for column, label in enumerate(labels, 1):
        cell = sheet.cell(row, column, label)
        cell.font = Font(name=FONT_NAME, size=BODY_SIZE, bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    sheet.row_dimensions[row].height = 30


def build(case=None, path=WORKBOOK_PATH):
    case = case or load_case()
    workbook = Workbook()
    workbook.remove(workbook.active)
    workbook.properties.creator = AUTHOR
    workbook.properties.lastModifiedBy = AUTHOR
    workbook.properties.title = "Party City 2023 Chapter 11 study"
    workbook.calculation = CalcProperties(calcId=191029, fullCalcOnLoad=True, forceFullCalc=True)
    for name in ("Waterfall", "Sensitivity", "Plan", "Capital", "Inputs"):
        sheet = workbook.create_sheet(name)
        sheet.sheet_view.showGridLines = False
        sheet.sheet_view.zoomScale = 90
        sheet.freeze_panes = "C5" if name == "Sensitivity" else "C11" if name == "Waterfall" else "B4"
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.paperSize = sheet.PAPERSIZE_A3
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0
        sheet.sheet_properties.tabColor = None
    inputs = workbook["Inputs"]
    inputs["A2"] = "Editable controls and source inputs (USD millions)"
    _header(inputs, 3, ["Driver", "Value", "Basis"])
    controls = [
        ("EV", scenario_values(case)["base"], "Midpoint of F25; model input"),
        ("DIP proxy", case["assumptions"]["dip_proxy_mm"], "F29 commitment used as claim proxy; not actual allowed DIP"),
        ("Cash adjustment", case["assumptions"]["cash_adjustment_mm"], "Assumption; actual estate cash unverified"),
        ("Administrative reserve", case["assumptions"]["administrative_reserve_mm"], "Assumption; actual costs unverified"),
        ("2024 forecast adjusted EBITDA", case["valuation"]["ebitda_2024_forecast_mm"], "F28, July forecast; not realized EBITDA"),
        ("Assumed exit net debt", case["valuation"]["assumed_exit_net_debt_mm"], "F27; used only for filed valuation bridge"),
        ("Stated low EV", case["valuation"]["ev_low_mm"], "F25"),
        ("Stated high EV", case["valuation"]["ev_high_mm"], "F25"),
        ("Reconciliation tolerance", case["assumptions"]["tolerance"], "Absolute, USD millions and decimal recovery; also fulcrum classification threshold"),
    ]
    for row, values in enumerate(controls, 4):
        for column, value in enumerate(values, 1):
            inputs.cell(row, column, value)
    nonnegative = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1=0)
    nonnegative.errorTitle = "Nonnegative amount required"
    nonnegative.error = "Enter a numeric value greater than or equal to zero."
    nonnegative.showErrorMessage = True
    nonnegative.errorStyle = "stop"
    inputs.add_data_validation(nonnegative)
    for coordinate in ("B4", "B5", "B7", "B8", "B10", "B11", "E15:E20"):
        nonnegative.add(coordinate)
    _header(inputs, 14, ["ID", "Tranche", "Class", "Rank", "Model principal", "Figure IDs"])
    tranches = [row for row in case["capital_structure"] if row["model_claim_mm"] is not None]
    for row, tranche in enumerate(tranches, FIRST_CLAIM_ROW):
        for column, value in enumerate([tranche["id"], tranche["tranche"], tranche["class"], tranche["rank"], tranche["model_claim_mm"], ", ".join(tranche["source_ids"])], 1):
            inputs.cell(row, column, value)
    _header(inputs, 23, ["Source ID", "Document", "URL", "Retrieved"])
    for row, (identifier, source) in enumerate(case["sources"].items(), 24):
        for column, value in enumerate([identifier, source["document"], source["url"], source["retrieved"]], 1):
            inputs.cell(row, column, value)
        inputs.cell(row, 3).hyperlink = source["url"]
        inputs.row_dimensions[row].height = 48
    inputs["A36"] = "Model scope"
    inputs["B36"] = case["assumptions"]["basis"]
    inputs.row_dimensions[36].height = 150
    inputs["A38"] = "ABL petition total"
    inputs["B38"] = next(row["petition_principal_mm"] for row in case["capital_structure"] if row["id"] == "abl_total")
    inputs["C38"] = "F02. Not the sum of July principal floors."
    inputs["A39"] = "July ABL principal floors"
    inputs["B39"] = "=SUM(E15:E16)"
    inputs["A40"] = "Difference to petition control"
    inputs["B40"] = "=B39-B38"

    plan = workbook["Plan"]
    plan["A2"] = "July 21 filed plan: projected recoveries, not realized distributions"
    _header(plan, 4, ["Class", "Name", "Low", "High", "Impairment", "Treatment", "Figure ID"])
    plan_rows = {}
    for row, record in enumerate(case["plan_recoveries"], 5):
        plan_rows[record["class"]] = row
        values = [record["class"], record["name"], record["low"] if record["low"] is not None else "N/A", record["high"] if record["high"] is not None else "N/A", record["impairment"], record["treatment"], record["figure_id"]]
        for column, value in enumerate(values, 1):
            plan.cell(row, column, value)
        plan.row_dimensions[row].height = 36
    plan["A16"] = "Class 4 components"
    plan["B16"] = "Direct equity 0.0%-0.08%; subscription rights 0.0%-7.53%. F22."
    plan["B17"] = "Rounded components do not exactly sum to reported 7.60%. Preserve reported totals."
    plan["A19"] = "Liquidation"
    plan["B19"] = "Unverified: Exhibit E omitted; Kroll HTTP 403. No numerical comparison."
    plan["A21"] = "Version"
    plan["B21"] = "Confirmation concerns a later fourth amended plan. July figures are not final-plan or actual recoveries."
    plan["A23"] = "Scope"
    plan["B23"] = "Classes 1, 2, 6 and 7 have no verified claim amounts and are excluded from numerical allocation."

    sheet = workbook["Waterfall"]
    sheet["A2"] = "Single-pool absolute priority (USD millions)"
    for row, label, formula in [(4, "Active EV", "=Inputs!B4"), (5, "Gross pool", "=MAX(0,B4+Inputs!B6)"),
                                 (6, "DIP and administrative reserve", "=Inputs!B5+Inputs!B7"), (7, "Available to modeled funded claims", "=MAX(0,B5-B6)")]:
        sheet.cell(row, 1, label)
        sheet.cell(row, 2, formula)
    _header(sheet, 10, ["Tranche", "Class", "Principal", "Ahead", "Rank total", "Payment", "Recovery", "Plan low", "Plan high", "Gap (pp)"])
    for row, source_row in enumerate(range(15, 21), 11):
        tranche = tranches[row - FIRST_WATERFALL_ROW]
        plan_row = plan_rows[tranche["class"]]
        formulas = [f"=Inputs!B{source_row}", f"=Inputs!C{source_row}", f"=Inputs!E{source_row}",
                    f'=SUMIF(Inputs!$D$15:$D$20,"<"&Inputs!D{source_row},Inputs!$E$15:$E$20)',
                    f'=SUMIF(Inputs!$D$15:$D$20,Inputs!D{source_row},Inputs!$E$15:$E$20)',
                    f'=IF(E{row}=0,0,MIN(MAX($B$7-D{row},0),E{row})*C{row}/E{row})',
                    f'=IF(C{row}=0,"N/A",F{row}/C{row})',
                    f"=Plan!C{plan_row}", f"=Plan!D{plan_row}",
                    f'=IF(C{row}=0,"N/A",(G{row}-MIN(MAX(G{row},H{row}),I{row}))*100)']
        for column, formula in enumerate(formulas, 1):
            sheet.cell(row, column, formula)
    sheet["A19"] = "Equity residual (USD mm)"
    sheet["B19"] = "=MAX(0,B7-SUM(F11:F16))"
    sheet["A20"] = "Conservation difference"
    sheet["B20"] = "=B5-MIN(B5,B6)-SUM(F11:F16)-B19"
    sheet["A21"] = "Active model fulcrum"
    sheet["B21"] = '=IF(AND(F11>Inputs!B12,F11<E11-Inputs!B12),"3A",IF(AND(F12>Inputs!B12,F12<E12-Inputs!B12),"3B",IF(AND(SUM(F13:F14)>Inputs!B12,SUM(F13:F14)<E13-Inputs!B12),"4",IF(AND(SUM(F15:F16)>Inputs!B12,SUM(F15:F16)<E15-Inputs!B12),"5 bonds only","No partially paid class"))))'
    _header(sheet, 24, ["Tranche", "Attachment EV", "Full-payment EV", "Meaning"])
    for row, model_row in enumerate(range(11, 17), 25):
        sheet.cell(row, 1, f"=A{model_row}")
        sheet.cell(row, 2, f"=MAX(0,$B$6-Inputs!B6+D{model_row})")
        sheet.cell(row, 3, f"=MAX(0,$B$6-Inputs!B6+D{model_row}+E{model_row})")
        sheet.cell(row, 4, "Principal impaired below full-payment EV; not legal plan impairment")
    _header(sheet, 33, ["Scenario", "EV", "Signed equity", "Floored equity", "3A recovery", "3B recovery", "4 recovery", "5 bonds only"])
    for row, label in enumerate(("low", "base", "high"), 34):
        sheet.cell(row, 1, label)
        sheet.cell(row, 2, "=Inputs!B10" if label == "low" else "=(Inputs!B10+Inputs!B11)/2" if label == "base" else "=Inputs!B11")
        sheet.cell(row, 3, f"=B{row}-Inputs!B9")
        sheet.cell(row, 4, f"=MAX(0,C{row})")
        for column, model_row in ((5, 11), (6, 12), (7, 13), (8, 15)):
            sheet.cell(row, column, f'=IF($E{model_row}=0,"N/A",MIN(MAX(MAX(0,$B{row}+Inputs!$B$6)-$B$6-$D{model_row},0),$E{model_row})/$E{model_row})')
    sheet["A39"] = "Filed equity bridge uses assumed exit net debt. It is separate from modeled principal allocation."
    sheet["A40"] = "Class 5 includes only two bond tranches. Classes 1 and 2 and estate costs lack verified denominators."
    sheet["A41"] = "Plan rights, dilution and settlements explain differences. See docs/methodology.md."

    sensitivity = workbook["Sensitivity"]
    sensitivity["A2"] = "EV = EBITDA x multiple; recoveries under the same modeled priority"
    _header(sensitivity, 4, ["EBITDA factor", "Multiple", "EBITDA", "EV", "3A recovery", "3B recovery", "4 recovery", "5 bonds only"])
    row = 5
    for factor in case["assumptions"]["ebitda_factors"]:
        for multiple in case["assumptions"]["multiples"]:
            sensitivity.cell(row, 1, factor)
            sensitivity.cell(row, 2, multiple)
            sensitivity.cell(row, 3, f"=Inputs!$B$8*A{row}")
            sensitivity.cell(row, 4, f"=B{row}*C{row}")
            for column, model_row in ((5, 11), (6, 12), (7, 13), (8, 15)):
                sensitivity.cell(row, column, f'=IF(Waterfall!$E${model_row}=0,"N/A",MIN(MAX(MAX(0,$D{row}+Inputs!$B$6)-Waterfall!$B$6-Waterfall!$D${model_row},0),Waterfall!$E${model_row})/Waterfall!$E${model_row})')
            row += 1
    sensitivity["A31"] = "Factors and multiples are analyst scenarios, not filing estimates. EBITDA is the July forecast for 2024."
    sensitivity["A32"] = "Explicit formulas are used instead of Excel What-If Data Tables to allow simple offline reconciliation."
    sensitivity["A33"] = "3A/3B use July principal floors. Class 5 covers bonds only. No liquidation sensitivity is fabricated."

    capital = workbook["Capital"]
    capital["A2"] = "Petition capital structure, January 17, 2023 (USD millions)"
    _header(capital, 4, ["Tranche", "Class", "Petition principal", "Model principal", "Maturity", "Coupon", "Security and priority", "Figure IDs"])
    for row, tranche in enumerate(case["capital_structure"], 5):
        values = [tranche["tranche"], tranche["class"], tranche["petition_principal_mm"] if tranche["petition_principal_mm"] is not None else "Unverified split", tranche["model_claim_mm"] if tranche["model_claim_mm"] is not None else "Control only", tranche["maturity"], tranche["coupon"], tranche["security"], ", ".join(tranche["source_ids"])]
        for column, value in enumerate(values, 1):
            capital.cell(row, column, value)
        capital.row_dimensions[row].height = 70
    capital["A14"] = "Model principals for 3A/3B are July plan floors, not verified petition splits. The aggregate ABL row is not added again."
    capital["A15"] = "Anagram intercompany facility: up to USD 22mm (F38); outstanding amount unverified, excluded."
    capital["A16"] = "Non-debtor Anagram debt, finance leases, trade and priority claims are outside the modeled funded-debt stack."
    widths = {
        "Waterfall": {"A": 35, "B": 20, "C": 20, "D": 21, "E": 15, "F": 15, "G": 16, "H": 16, "I": 15, "J": 14},
        "Sensitivity": {"A": 19, "B": 15, "C": 18, "D": 18, "E": 18, "F": 18, "G": 18, "H": 18},
        "Plan": {"A": 24, "B": 40, "C": 13, "D": 13, "E": 27, "F": 45, "G": 15},
        "Capital": {"A": 34, "B": 12, "C": 19, "D": 20, "E": 18, "F": 54, "G": 57, "H": 25},
        "Inputs": {"A": 35, "B": 47, "C": 95, "D": 17, "E": 20, "F": 35},
    }
    for sheet in workbook:
        for column, width in widths[sheet.title].items():
            sheet.column_dimensions[column].width = width
        for row in sheet:
            for cell in row:
                if cell.value is None:
                    continue
                if not cell.font.bold:
                    cell.font = Font(name=FONT_NAME, size=BODY_SIZE)
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                if isinstance(cell.value, (int, float)) or cell.data_type == "f":
                    cell.number_format = MONEY_FORMAT
        sheet["A2"].font = Font(name=FONT_NAME, size=14, bold=True)
        sheet["A2"].alignment = Alignment(wrap_text=False, vertical="center")
        sheet.row_dimensions[2].height = 24
        sheet.print_options.horizontalCentered = True
        sheet.print_area = f"A1:{sheet.cell(sheet.max_row, sheet.max_column).coordinate}"
    for row in range(11, 17):
        for column in (7, 8, 9):
            workbook["Waterfall"].cell(row, column).number_format = PERCENT_FORMAT
    for row in range(34, 37):
        for column in range(5, 9):
            workbook["Waterfall"].cell(row, column).number_format = PERCENT_FORMAT
    for row in range(5, 29):
        for column in range(5, 9):
            sensitivity.cell(row, column).number_format = PERCENT_FORMAT
    for row in range(5, 14):
        plan.cell(row, 3).number_format = PERCENT_FORMAT
        plan.cell(row, 4).number_format = PERCENT_FORMAT
    for row in range(25, 31):
        sheet = workbook["Waterfall"]
        sheet.row_dimensions[row].height = 36
    for coordinate in ("B16", "B17", "B19", "B21", "B23"):
        plan.merge_cells(start_row=plan[coordinate].row, start_column=2, end_row=plan[coordinate].row, end_column=7)
        plan.row_dimensions[plan[coordinate].row].height = 30
    inputs["B36"].alignment = Alignment(wrap_text=True, vertical="top")
    inputs.merge_cells("B36:F36")
    for name, rows, last_column in (("Waterfall", (39, 40, 41), 10), ("Sensitivity", (31, 32, 33), 8), ("Capital", (14, 15, 16), 8)):
        for row in rows:
            workbook[name].merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_column)
            workbook[name].row_dimensions[row].height = 28
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    return Path(path)


if __name__ == "__main__":
    print(build())
