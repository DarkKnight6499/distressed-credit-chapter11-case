# Capital structure

Petition date: 2023-01-17. USD millions of principal, not complete allowed claims. The ABL aggregate is a control row and must not be added again to the revolver and FILO rows.

| Tranche | Plan class | Petition principal | Model principal | Contractual maturity | Coupon | Security / priority | Evidence |
|---|---|---|---|---|---|---|---|
| ABL aggregate (control only) | 3A/3B | 424.3 | Control only | 2026-02-19 | See revolver and FILO | First lien on ABL collateral; second lien on other collateral | [F02](source_verification.md#f02), [F07](source_verification.md#f07) |
| ABL revolver | 3A | Unverified split | 407.282561 | 2026-02-19 | Adjusted Term SOFR + 1.50%-1.75% or ABR + 0.50%-0.75% | ABL collateral first lien; other collateral second lien | [F07](source_verification.md#f07), [F14](source_verification.md#f14), [F16](source_verification.md#f16), [F17](source_verification.md#f17) |
| ABL FILO | 3B | Unverified split | 17.1105 | 2026-02-19 | Adjusted Term SOFR + 2.75% or ABR + 1.75% | First-in last-out within ABL; model places after revolver | [F07](source_verification.md#f07), [F15](source_verification.md#f15), [F16](source_verification.md#f16), [F18](source_verification.md#f18) |
| Secured floating notes | 4 | 161.7 | 161.7 | 2025-07-15 | 6m LIBOR + 5.00%; LIBOR floor 0.75% | Other collateral first lien; ABL collateral second lien; pari passu with fixed notes | [F03](source_verification.md#f03), [F08](source_verification.md#f08), [F13](source_verification.md#f13) |
| Secured fixed notes | 4 | 750 | 750 | 2026-02-15 | 8.750% | Same liens and rank as floating notes | [F04](source_verification.md#f04), [F09](source_verification.md#f09), [F12](source_verification.md#f12) |
| Unsecured 2023 notes | 5 | 22.9 | 22.9 | 2023-08-15 | 6.125% | Senior unsecured; model pari passu with unsecured 2026 notes | [F05](source_verification.md#f05), [F10](source_verification.md#f10) |
| Unsecured 2026 notes | 5 | 92.3 | 92.3 | 2026-08-01 | 6.625% | Senior unsecured | [F06](source_verification.md#f06), [F11](source_verification.md#f11) |

The verified petition funded-principal control is USD 1,451.2 million ([D04](source_verification.md#d04)). The July revolver and FILO figures are principal floors plus additional allowed interest, fees and expenses, not a verified petition allocation. Their sum exceeds the rounded petition aggregate by USD 0.093061 million ([D10](source_verification.md#d10)). The project preserves this discrepancy instead of forcing equality.

Adjusted Term SOFR includes the credit adjustment in [F16](source_verification.md#f16); actual petition all-in floating rates and default interest are not reconstructed. Stated maturities are subject to contractual springing conditions and petition acceleration.

The Anagram intercompany facility has a maximum of USD 22 million, but no verified outstanding petition amount ([F38](source_verification.md#f38)). It is excluded from numerical allocation. Non-debtor Anagram debt is outside this debt stack. Other secured claims, priority claims, finance leases and trade claims are not represented by verified petition amounts. Old equity is residual and is canceled under the filed treatment ([F24](source_verification.md#f24)).
