"""Rebuild all offline artifacts and cache the tested Excel formula subset."""

import json
import sys
from pathlib import Path

# Configuration
ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = ROOT / "python"
WORKBOOK_PATH = ROOT / "excel/chapter11.xlsx"
VALIDATION_PATH = ROOT / "examples/output/formula_validation.json"
sys.path.insert(0, str(PACKAGE_DIRECTORY))

from openpyxl import load_workbook
from ch11.excel_eval import cache_values
from ch11.report import export
from ch11.workbook import build


def main():
    export()
    build(path=WORKBOOK_PATH)
    workbook = load_workbook(WORKBOOK_PATH)
    results = cache_values(WORKBOOK_PATH, workbook)
    workbook.close()
    VALIDATION_PATH.write_text(json.dumps({
        "method": "Restricted standard-library evaluator applied to stored Excel formula text",
        "formula_cells": len(results), "native_excel_recalculation": "untested",
        "native_attempt": "Excel COM failed with HRESULT 0x80070520: no logon session. Desktop UI native pipe also unavailable.",
        "tolerance": 1e-8,
        "note": "Caches are evaluated results. Live formulas remain; Excel is set to recalculate on open. Run unit tests for reconciliation and input perturbation."
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Built offline tables and workbook; evaluated {len(results)} live formulas.")


if __name__ == "__main__":
    main()
