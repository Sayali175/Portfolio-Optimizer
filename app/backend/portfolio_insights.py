
import math
from typing import Literal

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field, model_validator

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio Insights"],
)

ASSETS = ("equity", "debt", "hybrid", "liquid")

# Illustrative annual assumptions, NOT forecasts.
ANNUAL_RETURNS = {
    "equity": 0.10,
    "debt": 0.06,
    "hybrid": 0.08,
    "liquid": 0.04,
}

ANNUAL_VOLATILITY = {
    "equity": 0.18,
    "debt": 0.05,
    "hybrid": 0.11,
    "liquid": 0.01,
}

# Hypothetical simultaneous asset-class shocks.
STRESS_SCENARIOS = {
    "equity_crash": {
        "equity": -0.30,
        "debt": 0.02,
        "hybrid": -0.15,
        "liquid": 0.01,
    },
    "broad_market_downturn": {
        "equity": -0.20,
        "debt": -0.05,
        "hybrid": -0.12,
        "liquid": 0.00,
    },
    "interest_rate_shock": {
        "equity": -0.08,
        "debt": -0.10,
        "hybrid": -0.09,
        "liquid": 0.01,
    },
}


class HoldingInput(BaseModel):
    name: str = Field(min_length=1)
    asset_class: Literal[
        "equity", "debt", "hybrid", "liquid"
    ]
    current_value: float = Field(
        ge=0, allow_inf_nan=False
    )


class InsightsRequest(BaseModel):
    holdings: list[HoldingInput] = Field(min_length=1)
    target_weights: dict[str, float] | None = None
    horizon_years: int = Field(ge=1, le=50)
    goal_amount: float = Field(gt=0, allow_inf_nan=False)
    monthly_sip: float = Field(
        default=0, ge=0, allow_inf_nan=False
    )
    transaction_fee_rate: float = Field(
        default=0.001, ge=0, le=1
    )

    @model_validator(mode="after")
    def validate_target(self):
        if self.target_weights is not None:
            if set(self.target_weights) != set(ASSETS):
                raise ValueError(
                    "Target weights must contain all four asset classes"
                )

            values = list(self.target_weights.values())

            if not all(
                math.isfinite(v) and 0 <= v <= 1
                for v in values
            ):
                raise ValueError("Invalid target weights")

            if abs(sum(values) - 1) > 0.0001:
                raise ValueError(
                    "Target weights must sum to 1"
                )

        return self


def weighted_return(weights):
    return sum(
        weights[a] * ANNUAL_RETURNS[a]
        for a in ASSETS
    )


def calculate_goal(
    initial, monthly, years, annual_rate, target
):
    months = years * 12
    monthly_rate = (1 + annual_rate) ** (1 / 12) - 1

    growth = (1 + monthly_rate) ** months

    if abs(monthly_rate) < 1e-12:
        contribution_factor = months
    else:
        contribution_factor = (
            (growth - 1) / monthly_rate
        )

    projected = (
        initial * growth
        + monthly * contribution_factor
    )

    required_monthly = max(
        0,
        (target - initial * growth)
        / contribution_factor,
    )

    return {
        "target_amount": round(target, 2),
        "projected_value": round(projected, 2),
        "monthly_sip": round(monthly, 2),
        "required_monthly_sip": round(
            required_monthly, 2
        ),
        "goal_gap": round(
            max(0, target - projected), 2
        ),
        "assumed_annual_return": round(
            annual_rate, 4
        ),
    }


def future_scenarios(
    initial, monthly, years, weights
):
    # Illustrative Monte Carlo simulation.
    # Independent asset-class returns are a simplification.
    rng = np.random.default_rng(42)

    months = years * 12
    paths = 3000

    values = np.full(paths, initial, dtype=float)

    monthly_means = np.array([
        (1 + ANNUAL_RETURNS[a]) ** (1 / 12) - 1
        for a in ASSETS
    ])

    monthly_vols = np.array([
        ANNUAL_VOLATILITY[a] / math.sqrt(12)
        for a in ASSETS
    ])

    weight_vector = np.array([
        weights[a] for a in ASSETS
    ])

    for _ in range(months):
        asset_returns = rng.normal(
            loc=monthly_means,
            scale=monthly_vols,
            size=(paths, len(ASSETS)),
        )

        portfolio_returns = (
            asset_returns @ weight_vector
        )

        # Contributions are made at month end.
        values = (
            values * (1 + portfolio_returns)
            + monthly
        )

    p10, p50, p90 = np.percentile(
        values, [10, 50, 90]
    )

    return {
        "horizon_years": years,
        "simulations": paths,
        "downside_p10": round(float(p10), 2),
        "median_p50": round(float(p50), 2),
        "upside_p90": round(float(p90), 2),
        "method": "illustrative_monte_carlo",
    }


def stress_test(initial, weights):
    results = {}

    for name, shocks in STRESS_SCENARIOS.items():
        change = sum(
            weights[a] * shocks[a]
            for a in ASSETS
        )

        results[name] = {
            "portfolio_change": round(change, 4),
            "estimated_value": round(
                initial * (1 + change), 2
            ),
        }

    return results


@router.post("/insights")
def portfolio_insights(request: InsightsRequest):
    total = sum(
        h.current_value for h in request.holdings
    )

    if total <= 0:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail="Portfolio value must be positive",
        )

    amounts = {a: 0.0 for a in ASSETS}

    for holding in request.holdings:
        amounts[holding.asset_class] += (
            holding.current_value
        )

    current = {
        a: amounts[a] / total
        for a in ASSETS
    }

    target = request.target_weights

    response = {
        "portfolio_value": round(total, 2),
        "current_weights": current,
        "goal_planning": calculate_goal(
            total,
            request.monthly_sip,
            request.horizon_years,
            weighted_return(current),
            request.goal_amount,
        ),
        "future_scenarios": future_scenarios(
            total,
            request.monthly_sip,
            request.horizon_years,
            current,
        ),
        "stress_test": {
            "current": stress_test(total, current),
        },
        "assumptions": {
            "annual_returns": ANNUAL_RETURNS,
            "annual_volatility": ANNUAL_VOLATILITY,
            "stress_shocks": STRESS_SCENARIOS,
            "note": (
                "Illustrative assumptions, not "
                "market predictions or investment advice."
            ),
        },
    }

    if target is not None:
        changes = {}

        for asset in ASSETS:
            delta = total * (
                target[asset] - current[asset]
            )

            changes[asset] = {
                "current_amount": round(
                    amounts[asset], 2
                ),
                "target_amount": round(
                    total * target[asset], 2
                ),
                "adjustment": round(delta, 2),
                "action": (
                    "increase" if delta > 0.01
                    else "decrease" if delta < -0.01
                    else "hold"
                ),
            }

        gross_traded = sum(
            abs(item["adjustment"])
            for item in changes.values()
        )

        response["target_weights"] = target
        response["rebalancing"] = {
            "changes": changes,
            "estimated_transaction_fees": round(
                gross_traded
                * request.transaction_fee_rate,
                2,
            ),
            "estimated_tax": None,
            "tax_note": (
                "Purchase dates and cost basis are "
                "required to estimate taxes."
            ),
        }

        response["target_future_scenarios"] = (
            future_scenarios(
                total,
                request.monthly_sip,
                request.horizon_years,
                target,
            )
        )

        response["stress_test"]["target"] = (
            stress_test(total, target)
        )

    return response
