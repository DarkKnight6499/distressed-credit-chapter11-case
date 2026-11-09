"""Build provenance-linked case documentation from the offline snapshot."""

import hashlib
import json
import sys
from pathlib import Path

# Configuration
ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = ROOT / "python"
DOCS_DIRECTORY = ROOT / "docs"
NOTE_AUDIT_PATH = ROOT / "data/note_claims.json"
sys.path.insert(0, str(PACKAGE_DIRECTORY))

from ch11.model import case_claims, case_waterfall, thresholds
from ch11.report import load_case, scenario_values, tables


def display(value):
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value).replace("|", "/")


def link(identifier):
    return f"[{identifier}](source_verification.md#{identifier.lower()})"


def write(name, text):
    (DOCS_DIRECTORY / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def main():
    case = load_case()
    output = tables(case)
    values = scenario_values(case)
    base = case_waterfall(case, values["base"])
    high = case_waterfall(case, values["high"])
    claims = case_claims(case)
    senior_reserve = case["assumptions"]["dip_proxy_mm"] + case["assumptions"]["administrative_reserve_mm"]
    cutoffs = thresholds(claims, cash=case["assumptions"]["cash_adjustment_mm"], senior_cost=senior_reserve)
    secured = sum(claim.amount for claim in claims if claim.plan_class == "4")
    unsecured = sum(claim.amount for claim in claims if claim.plan_class == "5")
    petition = sum(row["petition_principal_mm"] or 0 for row in case["capital_structure"])
    derived = [
        ("D01", "Base EV (USD mm)", f'{values["base"]:.1f}', "(450 + 775) / 2", "F25"),
        ("D02", "Base secured recovery", f'{base["recoveries"]["secured_fixed"]:.2%}', "(base EV - DIP proxy - July ABL floors) / secured principal", "F03,F04,F17,F18,F25,F29; assumptions"),
        ("D03", "High secured recovery", f'{high["recoveries"]["secured_fixed"]:.2%}', "(high EV - DIP proxy - July ABL floors) / secured principal", "F03,F04,F17,F18,F25,F29; assumptions"),
        ("D04", "Petition funded principal control (USD mm)", f"{petition:,.1f}", "424.3 + 161.7 + 750 + 22.9 + 92.3", "F02-F06"),
        ("D05", "Secured principal (USD mm)", f"{secured:.1f}", "161.7 + 750", "F03,F04,F19"),
        ("D06", "Unsecured bond principal (USD mm)", f"{unsecured:.1f}", "22.9 + 92.3", "F05,F06"),
        ("D07", "Base filed-bridge equity (USD mm)", f'{values["base"] - case["valuation"]["assumed_exit_net_debt_mm"]:.1f}', "base EV - assumed exit net debt", "F25,F27"),
        ("D08", "Secured full-payment EV (USD mm)", f'{cutoffs["secured_fixed"]["full_recovery_ev"]:,.3f}', "DIP proxy + July ABL floors + secured principal", "F03,F04,F17,F18,F29; assumptions"),
        ("D09", "Base secured allocation (USD mm)", f'{sum(base["payments"][claim.identifier] for claim in claims if claim.plan_class == "4"):.6f}', "base EV - DIP proxy - July ABL floors", "F17,F18,F25,F29; assumptions"),
        ("D10", "July ABL floor minus petition control (USD mm)", f'{407.282561 + 17.1105 - 424.3:.6f}', "407.282561 + 17.1105 - 424.3", "F02,F17,F18"),
        ("D11", "High recovery excess over filed ceiling (percentage points)", f'{(high["recoveries"]["secured_fixed"] - .076)*100:.4f}', "high model recovery - reported 7.60% ceiling", "D03,F21"),
    ]
    lines = ["# Source verification", "", f'Retrieval date for every primary-source row: **{case["retrieval_date"]}**.', "",
             "Primary HTML documents were opened and read using the web tool. The shell was offline. Values were manually transcribed; full HTML archives were not downloaded. The manifest hashes the extracted snapshot, not the remote documents. A source figure marked verified is verified as a statement in that document, not as an eventual realized outcome.", "",
             "## Source access", "", "| ID | Document | URL | Retrieved | Result |", "|---|---|---|---|---|"]
    for identifier, source in case["sources"].items():
        lines.append(f'| {identifier} | {source["document"]} | [Open]({source["url"]}) | {source["retrieved"]} | Worked, primary document read |')
    lines += ["", "| Failed URL | Reason | Consequence |", "|---|---|---|",
              "| https://cases.ra.kroll.com/PCHI/ | HTTP 403 Forbidden from web open | Docket-dependent liquidation verification stopped |", "",
              "The SEC original disclosure statement opens successfully, but Exhibit E is intentionally omitted. That is a missing attachment, not a failed EDGAR fetch. The July supplement also omits its valuation attachment; the same updated valuation is readable in S03, Exhibit G. Search summaries and secondary sources were not used as evidence.", "",
              "## Verified extracted figures", "", "| ID | Figure | Value | Source URL | Document section / page | Retrieval date | Status |", "|---|---|---|---|---|---|---|"]
    for figure in case["verified_figures"]:
        source = case["sources"][figure["source_id"]]
        lines.append(f'| <a id="{figure["id"].lower()}"></a>{figure["id"]} | {figure["figure"]} | {display(figure["value"])} | [{figure["source_id"]}]({source["url"]}) | {figure["section"]} | {source["retrieved"]} | Verified in document |')
    lines += ["", "Collateral descriptions: S01, II.D.1-2, pp.10-11. Non-debtor Anagram scope: S01, II.C, p.9. Class treatment and impairment labels: S02, Exhibit A. Claim allowance includes accrued amounts in addition to the principal floors: S04, III.B.3-4. ABL stated maturities may spring earlier under financing terms: S10, Note 11. These are contractual maturity dates before acceleration, not post-petition payment dates.", "",
              "## Derived figures", "", "These are arithmetic or stylized model results, not additional source facts. Dependencies refer to verified rows above. All amounts are USD millions unless stated. Zero cash and administrative reserve are assumptions; the DIP commitment is a claim proxy.", "",
              "| ID | Result | Display value | Calculation | Dependencies |", "|---|---|---|---|---|"]
    for identifier, label, value, calculation, dependencies in derived:
        lines.append(f'| <a id="{identifier.lower()}"></a>{identifier} | {label} | {value} | {calculation} | {dependencies} |')
    lines += ["", "## Unverified and excluded", "", "| Field | Treatment |", "|---|---|"]
    for field in case["unverified"]:
        lines.append(f"| {field} | Not asserted as a verified result; unavailable or explicitly excluded/proxied |")
    lines += ["", "No liquidation recovery or proceeds are imputed. Blank liquidation CSV fields represent unavailable figures, not zeros.", "",
              "## Implementation controls", "", "The EV midpoint, zero cash adjustment, zero administrative reserve, EBITDA factors, sensitivity multiples and reconciliation tolerance are model controls. They are recorded in case_inputs.json under assumptions. The source note audit file binds every numeric token in the strategy note to a verified or derived row. Class numbers in the note are identifiers from the recovery table.", "",
              "## Findings for source practices", "", "SEC HTML works through the web tool. Read omitted exhibits in accompanying cleansing materials when available. S02's reported secured recovery total is 7.60%; rounded direct-equity and rights components are 0.08% and 7.53%, so their rounded sum is not an exact reconciliation. S04 supplies separately dated ABL principal floors; their sum differs from S01's rounded petition aggregate. Do not silently substitute one date or denominator for another."]
    write("source_verification.md", "\n".join(lines))

    capital_lines = ["# Capital structure", "", f'Petition date: {case["petition_date"]}. USD millions of principal, not complete allowed claims. The ABL aggregate is a control row and must not be added again to the revolver and FILO rows.', "",
                     "| Tranche | Plan class | Petition principal | Model principal | Contractual maturity | Coupon | Security / priority | Evidence |", "|---|---|---|---|---|---|---|---|"]
    for record in case["capital_structure"]:
        petition_value = str(record["petition_principal_mm"]) if record["petition_principal_mm"] is not None else "Unverified split"
        model_value = str(record["model_claim_mm"]) if record["model_claim_mm"] is not None else "Control only"
        capital_lines.append(f'| {record["tranche"]} | {record["class"]} | {petition_value} | {model_value} | {record["maturity"]} | {record["coupon"]} | {record["security"]} | {", ".join(link(i) for i in record["source_ids"])} |')
    capital_lines += ["", f'The verified petition funded-principal control is USD {petition:,.1f} million ({link("D04")}). The July revolver and FILO figures are principal floors plus additional allowed interest, fees and expenses, not a verified petition allocation. Their sum exceeds the rounded petition aggregate by USD {407.282561 + 17.1105 - 424.3:.6f} million ({link("D10")}). The project preserves this discrepancy instead of forcing equality.', "",
                      f'Adjusted Term SOFR includes the credit adjustment in {link("F16")}; actual petition all-in floating rates and default interest are not reconstructed. Stated maturities are subject to contractual springing conditions and petition acceleration.', "",
                      f'The Anagram intercompany facility has a maximum of USD 22 million, but no verified outstanding petition amount ({link("F38")}). It is excluded from numerical allocation. Non-debtor Anagram debt is outside this debt stack. Other secured claims, priority claims, finance leases and trade claims are not represented by verified petition amounts. Old equity is residual and is canceled under the filed treatment ({link("F24")}).']
    write("capital_structure.md", "\n".join(capital_lines))

    timeline = ["# Timeline", "", "Dates distinguish filing, approval and effectiveness. Court events below are verified through primary SEC filings; the underlying docket could not be opened.", "",
                "| Date | Event | Terms / context | Primary document and section |", "|---|---|---|---|"]
    for event in case["timeline"]:
        source = case["sources"][event["source_id"]]
        timeline.append(f'| {event["date"]} | {event["event"]} | {event["detail"]} | [{event["source_id"]}]({source["url"]}), {event["section"]}; {", ".join(link(i) for i in event["figure_ids"])} |')
    timeline += ["", "The July recovery table is retained as its own filed-plan vintage. Later confirmation and emergence do not validate those projected recovery percentages as actual distributions."]
    write("timeline.md", "\n".join(timeline))

    method = ["# Methodology and results", "", "## Separate dates and quantities", "",
              "Petition funded principal comes from the original disclosure statement. The ABL model uses the separate July plan principal floors because the petition split is unverified. Recovery percentages come from the July supplement, not the final confirmed plan. The valuation opinion is dated July 17, assumes a September 30 valuation date, and uses net debt assumed as of August 31. These dates are not treated as simultaneous realized balances.", "",
              "## Filed recovery table", "", "| Class | Name | Stated range | Impairment | Treatment | Evidence |", "|---|---|---|---|---|---|"]
    for record in case["plan_recoveries"]:
        recovery = "N/A" if record["low"] is None else f'{record["low"]:.2%} to {record["high"]:.2%}'
        method.append(f'| {record["class"]} | {record["name"]} | {recovery} | {record["impairment"]} | {record["treatment"]} | {link(record["figure_id"])} |')
    method += ["", "The secured-note range includes the separately reported direct-equity and subscription-right components in F22. Preserve the reported total and components, including their rounding difference. Class 5 receives the net GUC Recovery Pool. That settlement can pay unsecured claims while secured claims remain impaired. It is not reproduced by a single strict-priority cash pool.", "",
               "## Independent allocation", "", "For EV `V`, cash adjustment `C` and senior reserve `S = DIP proxy + administrative reserve`:", "",
               "```text\ngross_pool = max(0, V + C)\nfunded_pool = max(0, gross_pool - S)\ngroup_payment = min(group_claims, max(0, funded_pool - prior_rank_claims))\ntranche_payment = group_payment * tranche_claim / group_claims\nrecovery = tranche_payment / tranche_claim\nequity_residual = max(0, funded_pool - total_modeled_claims)\n```", "",
               "Zero-amount claims have no recovery denominator and return unavailable recovery. Within a rank, every positive claim receives the same percentage. The model conserves value, including the senior reserve and any equity residual. The default reserve uses the DIP commitment as a proxy; it does not model the allowed DIP claim or its negotiated conversion.", "",
               "## Valuation bridge and scenarios", "", "Method: use the stated advisor EV range. The base is its arithmetic midpoint. The EV/EBITDA ratios below divide by the July forecast for 2024; they are descriptive and do not reconstruct the advisor's valuation work.", "",
               "| Scenario | EV | Signed equity: EV less filed assumed net debt | Floored equity | EV / forecast EBITDA | Model 3A | Model 3B | Model 4 | Model 5 bonds only | Model fulcrum |", "|---|---|---|---|---|---|---|---|---|---|"]
    for row in output["valuation_bridge"]:
        by_class = {item["class"]: item["recovery"] for item in output["class_recoveries"] if item["scenario"] == row["scenario"]}
        method.append(f'| {row["scenario"]} | {row["ev_mm"]:.1f} | {row["signed_equity"]:.1f} | {row["equity"]:.1f} | {row["ev_to_2024_forecast_ebitda"]:.3f}x | {by_class["3A"]:.2%} | {by_class["3B"]:.2%} | {by_class["4"]:.2%} | {by_class["5"]:.2%} | {row["model_fulcrum"]} |')
    method += ["", "The filed net-debt bridge values the reorganized equity. The independent allocation values claims on the modeled prepetition stack after a senior reserve. Do not subtract exit net debt and also subtract the entire old debt stack from the same EV. The two calculations answer different questions.", "",
               "## Why recovery does not reconcile to the filed plan", "",
               f'Base modeled secured allocation is USD {sum(base["payments"][claim.identifier] for claim in claims if claim.plan_class == "4"):.6f} million, giving {base["recoveries"]["secured_fixed"]:.2%}. The high scenario gives {high["recoveries"]["secured_fixed"]:.2%}, or {(high["recoveries"]["secured_fixed"] - .076)*100:.4f} percentage points above the reported plan ceiling. Low EV impairs modeled ABL, although its projected plan recovery is full. All scenarios give the modeled unsecured bonds zero while the plan projects a positive GUC recovery. See D02, D03, D09 and D11 in the ledger.', "",
               "This is not a calibration error to remove with a plug. The plan refinances or takes back ABL; DIP holders may receive new securities; secured notes receive heavily diluted equity and valuable rights; rights require new money; unsecured recoveries arise from a negotiated trust. The model lacks the complete allowed-claim and collateral data needed to price that package. It neither values the rights nor treats purchased securities as free old-claim recovery. The modeled percentages are not substitutes for the plan's percentages.", "",
               "## Fulcrum and impairment thresholds", "",
               "Secured notes are the reorganization fulcrum in the selected plan because they exchange their claims for equity and rights. The strict-priority model's marginal class varies with EV: ABL revolver at low EV and secured notes at base and high EV. A fulcrum here means a positive but less than full principal recovery, not a legal determination of impairment.", "",
               "| Tranche | Attachment EV | Full-payment EV |", "|---|---|---|"]
    for record in output["thresholds"]:
        method.append(f'| {record["tranche"]} | {record["attachment_ev"]:.6f} | {record["full_recovery_ev"]:.6f} |')
    method += ["", "For each positive rank group, `attachment = max(0, senior reserve - cash + prior ranks)` and `full payment = max(0, attachment before flooring + group principal)`. Principal is economically impaired below the full-payment threshold. At attachment, payment is zero. At full payment, recovery equals par. No group is labeled partially paid at an exact boundary. Legal plan impairment can differ, as the ABL classes illustrate.", "",
               "## Sensitivity", "", "The live Excel grid combines the configured EBITDA factors and EV multiples. Each cell uses the same principal order and rank amounts as the active waterfall. The output CSV is long-form by class; it contains every factor/multiple/class combination. The following slice holds the forecast EBITDA unchanged.", "",
               "| EV multiple | EV | 3A | 3B | 4 | 5 bonds only |", "|---|---|---|---|---|---|"]
    for multiple in case["assumptions"]["multiples"]:
        group = [record for record in output["sensitivity"] if record["ebitda_factor"] == 1 and record["multiple"] == multiple]
        recoveries = {record["class"]: record["recovery"] for record in group}
        method.append(f'| {multiple:.1f}x | {multiple * case["valuation"]["ebitda_2024_forecast_mm"]:.2f} | {recoveries["3A"]:.2%} | {recoveries["3B"]:.2%} | {recoveries["4"]:.2%} | {recoveries["5"]:.2%} |')
    method += ["", "## Liquidation versus reorganization", "", "Unavailable. The liquidation analysis is identified as Exhibit E to the original disclosure statement but intentionally omitted from the EDGAR attachment. Kroll returned HTTP 403. The advisor's reorganization range is verified; no liquidation proceeds, liquidation recovery, or reorganization premium to liquidation can be calculated. The liquidation comparison CSV records every class as unavailable. No reorganization EV is relabeled as a liquidation value.", "",
               "## Excel reconciliation", "", "All live formulas are evaluated using a restricted standard-library engine. Tests compare every scenario/class recovery, sensitivity recovery, tranche payment, recovery fraction, threshold and equity bridge to Python. They also change EV, cash, DIP, administrative reserve, claim amounts and forecast EBITDA. Absolute tolerance is 1e-8 in USD millions and decimal recoveries. Formula caches are populated from evaluated formulas, not copied Python outputs. The snapshot has its own SHA-256 check.", "",
               "Native Excel COM startup failed with HRESULT 0x80070520. No native recalculation or visual review is claimed. Excel is set to recalculate on open, and a local PowerShell recalculation script is included. See limitations.md for model and implementation boundaries."]
    write("methodology.md", "\n".join(method))

    paragraphs = [
        ("# Party City restructuring: retrospective desk note", [], []),
        ("This is a retrospective study, not investment advice. The analytical vintage is the third amended plan dated 2023-07-21. Confirmation and emergence occurred later; projected recoveries below are not realized distributions.", ["F34"], ["2023-07-21"]),
        ("**Situation.** Liquidity pressure led to a debt-for-equity restructuring. The analytical question is whether value accrues to the old claim, to new financing, or to subscription rights. A simple enterprise-value waterfall cannot price all three. Keep financing participation and old-claim consideration separate.", [], []),
        (f'**Capital structure.** Petition funded principal totals USD {petition:,.1f} million: USD 424.3 million ABL, USD {secured:.1f} million secured notes and USD {unsecured:.1f} million unsecured bonds. The ABL has priority over receivables and inventory; the notes have first liens on other collateral. Both secured-note issues share the modeled fulcrum rank. July ABL floors replace the unverified petition split in the numerical model.', ["D04", "F02", "D05", "D06"], [f"{petition:,.1f}", "424.3", f"{secured:.1f}", f"{unsecured:.1f}"]),
        (f'**Valuation and fulcrum.** The stated EV range is USD 450 million to USD 775 million. The arithmetic base is USD {values["base"]:.1f} million. Filed assumed exit net debt is USD 513 million, giving base reorganized equity of USD {values["base"] - 513:.1f} million. The standalone priority model gives secured notes {base["recoveries"]["secured_fixed"]:.2%} at base and {high["recoveries"]["secured_fixed"]:.2%} at high EV. Those results depend on the DIP proxy and omitted estate costs. Secured notes are the plan fulcrum; at low EV, the model instead places the marginal loss in ABL.', ["F25", "D01", "F27", "D07", "D02", "D03"], ["450", "775", f'{values["base"]:.1f}', "513", f'{values["base"] - 513:.1f}', f'{base["recoveries"]["secured_fixed"]:.2%}', f'{high["recoveries"]["secured_fixed"]:.2%}']),
        ("**Filed consideration.** Projected secured-note recovery is 0.0%-7.60%. The filing separately attributes 0.0%-0.08% to direct equity and 0.0%-7.53% to subscription rights. Rounded components do not exactly add to the reported ceiling. General unsecured recovery is projected at 1.0%-2.5%, despite the strict-priority model paying the bond subset nothing. Rights, dilution and the negotiated GUC pool explain why priority alone does not reproduce the filed economics.", ["F21", "F22", "F23"], ["0.0%", "7.60%", "0.08%", "7.53%", "1.0%", "2.5%"]),
        ("**Trade framing.** ABL exposure expresses a refinancing and collateral-coverage view, with borrowing-base and execution risk. Secured notes express a recovery-and-rights view: distinguish the floating and fixed coupons, and assess participation cash, dilution, transfer restrictions and exit security liquidity before comparing claims. Unsecured bonds express a settlement-pool view, with uncertain allowed claims, trust expenses and timing. Old common has no distribution under the filed treatment. No entry prices or return estimates are supplied because verified trading data is absent.", ["F24"], []),
        ("**What changes the view.** Revise for stronger cash generation, weaker inventory realizations, a larger priority reserve, a different DIP takeout, changed rights economics or a larger unsecured denominator. A complete collateral and claims reconciliation would matter more than a finer EV increment. Liquidation downside remains unverified because the source attachment is omitted and the claims-agent docket is blocked. The model cannot establish a liquidation floor.", [], []),
    ]
    note_lines = []
    audit = []
    for paragraph, evidence, tokens in paragraphs:
        note_lines.append(paragraph + (" " + ", ".join(link(identifier) for identifier in evidence) + "." if evidence else ""))
        audit.extend({"token": token, "evidence": evidence, "paragraph_sha256": hashlib.sha256(paragraph.encode()).hexdigest()} for token in tokens)
    write("strategy_note.md", "\n\n".join(note_lines))
    NOTE_AUDIT_PATH.write_text(json.dumps({"note": "docs/strategy_note.md", "claims": audit,
                                           "method": "Each numeric display token maps to ledger rows; derived rows are generated from the same reviewed inputs."}, indent=2) + "\n", encoding="utf-8")
    print("Built source ledger, capital structure, timeline, methodology and audited strategy note.")


if __name__ == "__main__":
    main()
