"""Principal-only, single-pool absolute-priority model. Amounts are USD millions."""

from dataclasses import dataclass
from math import isfinite

# Configuration
BOUNDARY_TOLERANCE = 1e-8


@dataclass(frozen=True)
class Claim:
    identifier: str
    amount: float
    rank: int
    plan_class: str


def _finite(value, label, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    if not isfinite(value) or (nonnegative and value < 0):
        raise ValueError(f"Invalid {label}")


def validate_claims(claims):
    claims = tuple(claims)
    seen = set()
    for claim in claims:
        if not claim.identifier or claim.identifier in seen:
            raise ValueError("Claim identifiers must be unique and nonempty")
        seen.add(claim.identifier)
        _finite(claim.amount, "claim amount", True)
        if isinstance(claim.rank, bool) or not isinstance(claim.rank, int) or claim.rank < 1:
            raise ValueError("Rank must be a positive integer")
    return claims


def waterfall(ev, claims, cash=0.0, senior_cost=0.0):
    """Pay rank groups in order and allocate within each group pro rata."""
    _finite(ev, "EV", True)
    _finite(cash, "cash adjustment")
    _finite(senior_cost, "senior cost", True)
    claims = validate_claims(claims)
    pool = max(0.0, ev + cash)
    senior_paid = min(pool, senior_cost)
    remaining = pool - senior_paid
    payments = {}
    recoveries = {}
    fulcrum = []
    for rank in sorted({claim.rank for claim in claims}):
        group = [claim for claim in claims if claim.rank == rank]
        total = sum(claim.amount for claim in group)
        payout = min(remaining, total)
        fraction = payout / total if total else None
        for claim in group:
            payments[claim.identifier] = claim.amount * fraction if total else 0.0
            recoveries[claim.identifier] = fraction if claim.amount else None
        if fraction is not None and BOUNDARY_TOLERANCE < payout < total - BOUNDARY_TOLERANCE:
            fulcrum = [claim.identifier for claim in group if claim.amount]
        remaining = max(0.0, remaining - payout)
    return {"pool": pool, "senior_paid": senior_paid,
            "senior_shortfall": senior_cost - senior_paid, "payments": payments,
            "recoveries": recoveries, "equity": remaining, "fulcrum": fulcrum}


def thresholds(claims, cash=0.0, senior_cost=0.0):
    """Return attachment and full-payment EV for each pari passu rank group."""
    _finite(cash, "cash adjustment")
    _finite(senior_cost, "senior cost", True)
    claims = validate_claims(claims)
    ahead = senior_cost - cash
    results = {}
    for rank in sorted({claim.rank for claim in claims}):
        group = [claim for claim in claims if claim.rank == rank]
        total = sum(claim.amount for claim in group)
        for claim in group:
            results[claim.identifier] = {"attachment_ev": max(0.0, ahead),
                                         "full_recovery_ev": max(0.0, ahead + total)}
        ahead += total
    return results


def equity_bridge(ev, net_debt):
    _finite(ev, "EV", True)
    _finite(net_debt, "net debt")
    signed = ev - net_debt
    return {"signed_equity": signed, "equity": max(0.0, signed)}


def case_claims(case):
    return tuple(Claim(row["id"], row["model_claim_mm"], row["rank"], row["class"])
                 for row in case["capital_structure"] if row["model_claim_mm"] is not None)


def case_waterfall(case, ev):
    assumptions = case["assumptions"]
    return waterfall(ev, case_claims(case), assumptions["cash_adjustment_mm"],
                     assumptions["dip_proxy_mm"] + assumptions["administrative_reserve_mm"])
