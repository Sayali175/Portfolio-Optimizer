
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio Management"],
)

AssetClass = Literal[
    "equity",
    "debt",
    "hybrid",
    "liquid",
]

RiskTolerance = Literal[
    "conservative",
    "moderate",
    "aggressive",
]

RISK_MAP = {
    "conservative": 0.1,
    "moderate": 0.5,
    "aggressive": 0.9,
}


class Holding(BaseModel):
    name: str = Field(min_length=1)
    asset_class: AssetClass
    current_value: float = Field(ge=0, allow_inf_nan=False)


class PortfolioRequest(BaseModel):
    initial_balance: float = Field(gt=0, allow_inf_nan=False)
    goal: Literal["wealth", "retirement", "savings"]
    risk_tolerance: RiskTolerance
    investment_horizon_years: int = Field(ge=1, le=50)
    holdings: list[Holding] = Field(min_length=1)


@router.post("/analyze")
def analyze_portfolio(request: PortfolioRequest):

    total_holdings = sum(
        holding.current_value
        for holding in request.holdings
    )

    if abs(total_holdings - request.initial_balance) > 0.01:
        raise HTTPException(
            status_code=422,
            detail="Total holdings must match portfolio balance.",
        )

    allocation = {
        "equity": 0.0,
        "debt": 0.0,
        "hybrid": 0.0,
        "liquid": 0.0,
    }

    for holding in request.holdings:
        allocation[holding.asset_class] += (
            holding.current_value / total_holdings
        )

    return {
        "status": "ready_for_optimization",
        "portfolio_value": round(total_holdings, 2),
        "goal": request.goal,
        "investment_horizon_years": (
            request.investment_horizon_years
        ),
        "risk_profile": RISK_MAP[request.risk_tolerance],
        "current_weights": {
            asset: round(weight, 6)
            for asset, weight in allocation.items()
        },
    }
