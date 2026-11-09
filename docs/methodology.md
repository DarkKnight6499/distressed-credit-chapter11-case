# Methodology and results

## Separate dates and quantities

Petition funded principal comes from the original disclosure statement. The ABL model uses the separate July plan principal floors because the petition split is unverified. Recovery percentages come from the July supplement, not the final confirmed plan. The valuation opinion is dated July 17, assumes a September 30 valuation date, and uses net debt assumed as of August 31. These dates are not treated as simultaneous realized balances.

## Filed recovery table

| Class | Name | Stated range | Impairment | Treatment | Evidence |
|---|---|---|---|---|---|
| 1 | Other secured | 100.00% to 100.00% | Unimpaired | Cash, reinstatement or permitted alternative | [F20](source_verification.md#f20) |
| 2 | Other priority | 100.00% to 100.00% | Unimpaired | Cash or statutory treatment | [F20](source_verification.md#f20) |
| 3A | ABL revolver | 100.00% to 100.00% | Impaired | Takeback or exit refinancing | [F20](source_verification.md#f20) |
| 3B | ABL FILO | 100.00% to 100.00% | Impaired | Takeback or exit refinancing | [F20](source_verification.md#f20) |
| 4 | Secured notes | 0.00% to 7.60% | Impaired | Diluted equity and subscription rights | [F21](source_verification.md#f21) |
| 5 | General unsecured | 1.00% to 2.50% | Impaired | GUC Recovery Pool | [F23](source_verification.md#f23) |
| 6 | Intercompany claims | N/A | Unimpaired / Impaired | Reinstate or cancel | [F24](source_verification.md#f24) |
| 7 | Intercompany interests | N/A | Unimpaired / Impaired | Reinstate or cancel | [F24](source_verification.md#f24) |
| 8 | PCHI interests | 0.00% to 0.00% | Impaired | Cancel, no distribution | [F24](source_verification.md#f24) |

The secured-note range includes the separately reported direct-equity and subscription-right components in F22. Preserve the reported total and components, including their rounding difference. Class 5 receives the net GUC Recovery Pool. That settlement can pay unsecured claims while secured claims remain impaired. It is not reproduced by a single strict-priority cash pool.

## Independent allocation

For EV `V`, cash adjustment `C` and senior reserve `S = DIP proxy + administrative reserve`:

```text
gross_pool = max(0, V + C)
funded_pool = max(0, gross_pool - S)
group_payment = min(group_claims, max(0, funded_pool - prior_rank_claims))
tranche_payment = group_payment * tranche_claim / group_claims
recovery = tranche_payment / tranche_claim
equity_residual = max(0, funded_pool - total_modeled_claims)
```

Zero-amount claims have no recovery denominator and return unavailable recovery. Within a rank, every positive claim receives the same percentage. The model conserves value, including the senior reserve and any equity residual. The default reserve uses the DIP commitment as a proxy; it does not model the allowed DIP claim or its negotiated conversion.

## Valuation bridge and scenarios

Method: use the stated advisor EV range. The base is its arithmetic midpoint. The EV/EBITDA ratios below divide by the July forecast for 2024; they are descriptive and do not reconstruct the advisor's valuation work.

| Scenario | EV | Signed equity: EV less filed assumed net debt | Floored equity | EV / forecast EBITDA | Model 3A | Model 3B | Model 4 | Model 5 bonds only | Model fulcrum |
|---|---|---|---|---|---|---|---|---|---|
| low | 450.0 | -63.0 | 0.0 | 3.250x | 73.66% | 0.00% | 0.00% | 0.00% | revolver |
| base | 612.5 | 99.5 | 99.5 | 4.424x | 100.00% | 100.00% | 4.18% | 0.00% | secured_float; secured_fixed |
| high | 775.0 | 262.0 | 262.0 | 5.598x | 100.00% | 100.00% | 22.00% | 0.00% | secured_float; secured_fixed |

The filed net-debt bridge values the reorganized equity. The independent allocation values claims on the modeled prepetition stack after a senior reserve. Do not subtract exit net debt and also subtract the entire old debt stack from the same EV. The two calculations answer different questions.

## Why recovery does not reconcile to the filed plan

Base modeled secured allocation is USD 38.106939 million, giving 4.18%. The high scenario gives 22.00%, or 14.4036 percentage points above the reported plan ceiling. Low EV impairs modeled ABL, although its projected plan recovery is full. All scenarios give the modeled unsecured bonds zero while the plan projects a positive GUC recovery. See D02, D03, D09 and D11 in the ledger.

This is not a calibration error to remove with a plug. The plan refinances or takes back ABL; DIP holders may receive new securities; secured notes receive heavily diluted equity and valuable rights; rights require new money; unsecured recoveries arise from a negotiated trust. The model lacks the complete allowed-claim and collateral data needed to price that package. It neither values the rights nor treats purchased securities as free old-claim recovery. The modeled percentages are not substitutes for the plan's percentages.

## Fulcrum and impairment thresholds

Secured notes are the reorganization fulcrum in the selected plan because they exchange their claims for equity and rights. The strict-priority model's marginal class varies with EV: ABL revolver at low EV and secured notes at base and high EV. A fulcrum here means a positive but less than full principal recovery, not a legal determination of impairment.

| Tranche | Attachment EV | Full-payment EV |
|---|---|---|
| revolver | 150.000000 | 557.282561 |
| filo | 557.282561 | 574.393061 |
| secured_float | 574.393061 | 1486.093061 |
| secured_fixed | 574.393061 | 1486.093061 |
| unsecured_2023 | 1486.093061 | 1601.293061 |
| unsecured_2026 | 1486.093061 | 1601.293061 |

For each positive rank group, `attachment = max(0, senior reserve - cash + prior ranks)` and `full payment = max(0, attachment before flooring + group principal)`. Principal is economically impaired below the full-payment threshold. At attachment, payment is zero. At full payment, recovery equals par. No group is labeled partially paid at an exact boundary. Legal plan impairment can differ, as the ABL classes illustrate.

## Sensitivity

The live Excel grid combines the configured EBITDA factors and EV multiples. Each cell uses the same principal order and rank amounts as the active waterfall. The output CSV is long-form by class; it contains every factor/multiple/class combination. The following slice holds the forecast EBITDA unchanged.

| EV multiple | EV | 3A | 3B | 4 | 5 bonds only |
|---|---|---|---|---|---|
| 2.0x | 276.90 | 31.16% | 0.00% | 0.00% | 0.00% |
| 3.0x | 415.35 | 65.15% | 0.00% | 0.00% | 0.00% |
| 4.0x | 553.80 | 99.14% | 0.00% | 0.00% | 0.00% |
| 5.0x | 692.25 | 100.00% | 100.00% | 12.93% | 0.00% |
| 6.0x | 830.70 | 100.00% | 100.00% | 28.11% | 0.00% |
| 8.0x | 1107.60 | 100.00% | 100.00% | 58.48% | 0.00% |
| 10.0x | 1384.50 | 100.00% | 100.00% | 88.86% | 0.00% |
| 12.0x | 1661.40 | 100.00% | 100.00% | 100.00% | 100.00% |

## Liquidation versus reorganization

Unavailable. The liquidation analysis is identified as Exhibit E to the original disclosure statement but intentionally omitted from the EDGAR attachment. Kroll returned HTTP 403. The advisor's reorganization range is verified; no liquidation proceeds, liquidation recovery, or reorganization premium to liquidation can be calculated. The liquidation comparison CSV records every class as unavailable. No reorganization EV is relabeled as a liquidation value.

## Excel reconciliation

All live formulas are evaluated using a restricted standard-library engine. Tests compare every scenario/class recovery, sensitivity recovery, tranche payment, recovery fraction, threshold and equity bridge to Python. They also change EV, cash, DIP, administrative reserve, claim amounts and forecast EBITDA. Absolute tolerance is 1e-8 in USD millions and decimal recoveries. Formula caches are populated from evaluated formulas, not copied Python outputs. The snapshot has its own SHA-256 check.

Native Excel COM startup failed with HRESULT 0x80070520. No native recalculation or visual review is claimed. Excel is set to recalculate on open, and a local PowerShell recalculation script is included. See limitations.md for model and implementation boundaries.
