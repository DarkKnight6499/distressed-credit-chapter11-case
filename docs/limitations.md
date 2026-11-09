# Limitations

## Stylized

- One pooled estate. No debtor-by-debtor guarantees, collateral values, intercreditor enforcement or structural subordination model.
- Revolver, then FILO, then secured notes, then unsecured bonds. Crossed liens are simplified into that order.
- Principal-only recoveries. No accrued interest, fees, default interest, make-whole litigation, taxes, timing discount or exit security pricing.
- The two secured tranches share one rank. The two unsecured bonds share one rank. Class 5's modeled denominator excludes trade, lease rejection and other general unsecured claims.
- Class 1, Class 2 and intercompany classes lack verified denominators and receive no numerical allocation. Their omission is not evidence that their claims are zero.

## Assumptions and estimates

- Base EV is the arithmetic midpoint of the advisor's stated range. It is not a filed base valuation.
- EBITDA factors and multiples are analyst scenarios, not advisor-selected comparable multiples. The EBITDA input is a forecast, not a realized result.
- The DIP commitment is used as a claim proxy. Actual drawn and allowed amounts, premiums and accrued interest are not reconstructed.
- Cash adjustment and administrative reserve default to zero. Those defaults overstate available funded-creditor value if actual omitted net costs are positive.
- July ABL principal floors are model inputs. They are separately dated from the rounded petition aggregate and do not resolve the petition split.

## Not verified

Liquidation proceeds and recoveries; actual estate cash; complete priority, administrative, lease and unsecured claims; allowed DIP claim amounts; petition ABL split; outstanding Anagram intercompany loan; petition finance lease claims; final-plan recovery table; actual distributions and trading prices.

The liquidation exhibit is omitted from the EDGAR disclosure statement. The Kroll docket was blocked. The project preserves nulls and unavailable outputs. It does not substitute reorganization EV for liquidation proceeds.

The strategy frames possible exposures without live prices, entry levels, return forecasts or actionable recommendations. This is a retrospective study, not investment advice. There is no claim of real-world validation.

## Implementation verification

The restricted evaluator supports only the formula functions used in this workbook. It checks saved formula text against Python and stores calculated caches. It is not a general Excel engine. Input changes are tested through that evaluator. Native Excel COM could not start because no Windows logon session existed. The desktop UI native pipe was also unavailable. Native recalculation, Excel UI rendering and visual print review remain untested.
