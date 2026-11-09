"""Reproduce the case tables from the checked-in snapshot without network access."""

import csv
import json
from pathlib import Path

from .model import case_claims, case_waterfall, equity_bridge, thresholds

# Configuration
ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = ROOT / "data/case_inputs.json"
OUTPUT_DIRECTORY = ROOT / "examples/output"
CASE_COLUMN = "scenario"
EV_COLUMN = "ev_mm"
TRANCHE_COLUMN = "tranche"
RECOVERY_COLUMN = "recovery"


def load_case(path=SNAPSHOT_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def scenario_values(case):
    valuation = case["valuation"]
    low, high = valuation["ev_low_mm"], valuation["ev_high_mm"]
    return {"low": low, "base": (low + high) / 2, "high": high}


def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def tables(case):
    claims = case_claims(case)
    plan = {row["class"]: row for row in case["plan_recoveries"]}
    outputs = {"capital_structure": case["capital_structure"],
               "plan_recoveries": case["plan_recoveries"],
               "timeline": [{**row, "url": case["sources"][row["source_id"]]["url"]} for row in case["timeline"]]}
    scenarios, bridge, class_rows = [], [], []
    for label, ev in scenario_values(case).items():
        result = case_waterfall(case, ev)
        for claim in claims:
            recovery = result["recoveries"][claim.identifier]
            stated = plan[claim.plan_class]
            scenarios.append({CASE_COLUMN: label, EV_COLUMN: ev, TRANCHE_COLUMN: claim.identifier,
                              "plan_class": claim.plan_class, "claim_mm": claim.amount,
                              "payout_mm": result["payments"][claim.identifier], RECOVERY_COLUMN: recovery,
                              "plan_low": stated["low"], "plan_high": stated["high"],
                              "gap_to_nearest_plan_bound": recovery - min(max(recovery, stated["low"]), stated["high"])})
        for plan_class in ("3A", "3B", "4", "5"):
            group = [claim for claim in claims if claim.plan_class == plan_class]
            total = sum(claim.amount for claim in group)
            class_rows.append({CASE_COLUMN: label, EV_COLUMN: ev, "class": plan_class,
                               "scope": "bond-only proxy" if plan_class == "5" else "modeled principal",
                               RECOVERY_COLUMN: sum(result["payments"][claim.identifier] for claim in group) / total})
        bridge.append({CASE_COLUMN: label, EV_COLUMN: ev,
                       "assumed_net_debt_mm": case["valuation"]["assumed_exit_net_debt_mm"],
                       **equity_bridge(ev, case["valuation"]["assumed_exit_net_debt_mm"]),
                       "model_senior_paid_mm": result["senior_paid"],
                       "model_equity_mm": result["equity"], "model_fulcrum": "; ".join(result["fulcrum"]),
                       "ev_to_2024_forecast_ebitda": ev / case["valuation"]["ebitda_2024_forecast_mm"]})
    outputs["scenario_recoveries"] = scenarios
    outputs["class_recoveries"] = class_rows
    outputs["valuation_bridge"] = bridge
    assumptions = case["assumptions"]
    outputs["thresholds"] = [{TRANCHE_COLUMN: claim.identifier, "class": claim.plan_class, **threshold}
                             for claim in claims
                             for threshold in [thresholds(claims, assumptions["cash_adjustment_mm"],
                                                          assumptions["dip_proxy_mm"] + assumptions["administrative_reserve_mm"])[claim.identifier]]]
    sensitivity = []
    for factor in assumptions["ebitda_factors"]:
        ebitda = factor * case["valuation"]["ebitda_2024_forecast_mm"]
        for multiple in assumptions["multiples"]:
            ev = ebitda * multiple
            result = case_waterfall(case, ev)
            for plan_class in ("3A", "3B", "4", "5"):
                group = [claim for claim in claims if claim.plan_class == plan_class]
                sensitivity.append({"ebitda_factor": factor, "ebitda_mm": ebitda, "multiple": multiple,
                                    EV_COLUMN: ev, "class": plan_class,
                                    "scope": "bond-only proxy" if plan_class == "5" else "modeled principal",
                                    RECOVERY_COLUMN: sum(result["payments"][claim.identifier] for claim in group) / sum(claim.amount for claim in group)})
    outputs["sensitivity"] = sensitivity
    outputs["liquidation_comparison"] = [{"class": row["class"], "filed_liquidation_recovery": None,
                                            "status": case["liquidation"]["status"],
                                            "reason": case["liquidation"]["reason"]} for row in case["plan_recoveries"]]
    return outputs


def export(case=None, directory=OUTPUT_DIRECTORY):
    case = case or load_case()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    outputs = tables(case)
    for name, rows in outputs.items():
        write_csv(directory / f"{name}.csv", rows)
    (directory / "results.json").write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
    return outputs


if __name__ == "__main__":
    export()
