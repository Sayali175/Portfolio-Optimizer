
import numpy as np
import pandas as pd

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from stable_baselines3 import PPO

from app.backend.portfolio import (
    Holding,
    RiskTolerance,
    RISK_MAP,
)

from app.backend.portfolio_insights import (
    InsightsRequest,
    portfolio_insights,
)

from app.backend.explainability import (
    create_explanations,
    analyze_model_sensitivity,
)


# ---------------------------------------------------------
# ASSET CLASSES
# ---------------------------------------------------------

ASSETS = (
    "equity",
    "debt",
    "hybrid",
    "liquid",
)


# ---------------------------------------------------------
# MARKET FEATURES
# ---------------------------------------------------------

MARKET_FEATURES = [
    "equity_return",
    "debt_return",
    "hybrid_return",
    "liquid_return",
    "equity_vol_30d",
    "debt_vol_30d",
    "hybrid_vol_30d",
    "liquid_vol_30d",
    "nifty_return",
    "nifty_vol_30d",
    "nifty_rsi_14",
    "nifty_sma_ratio",
    "nifty_macd_diff",
]


# ---------------------------------------------------------
# REQUEST MODEL
# ---------------------------------------------------------

class PersonalizedRequest(BaseModel):

    holdings: list[Holding] = Field(
        min_length=1
    )

    risk_tolerance: RiskTolerance = (
        "moderate"
    )

    investment_horizon_years: int = Field(
        ge=1,
        le=50,
    )

    goal_amount: float = Field(
        gt=0,
        allow_inf_nan=False,
    )

    monthly_sip: float = Field(
        default=0,
        ge=0,
        allow_inf_nan=False,
    )


# ---------------------------------------------------------
# HELPER: SOFTMAX ALLOCATION
# ---------------------------------------------------------

def convert_action_to_weights(action):
    """
    Convert four PPO actions into portfolio weights.

    Must match the action-to-allocation transformation
    used in explainability.py and PortfolioEnvV2.
    """

    action = np.asarray(
        action,
        dtype=np.float64,
    ).reshape(-1)

    if (
        action.shape != (4,)
        or not np.isfinite(action).all()
    ):
        raise ValueError(
            "PPO returned an invalid action."
        )

    action = np.clip(
        action,
        -5.0,
        5.0,
    )

    exp_action = np.exp(
        action - np.max(action)
    )

    weights = (
        exp_action / exp_action.sum()
    )

    return weights


# ---------------------------------------------------------
# CREATE PERSONALIZED ROUTER
# ---------------------------------------------------------

def create_personalized_router(
    model: PPO,
    market_data: pd.DataFrame,
):

    router = APIRouter(
        prefix="/portfolio",
        tags=["Personalized Optimization"],
    )

    # -----------------------------------------------------
    # OPTIMIZE PORTFOLIO
    # -----------------------------------------------------

    @router.post("/optimize")
    def optimize_portfolio(
        request: PersonalizedRequest,
    ):

        # -------------------------------------------------
        # STEP 1: CALCULATE TOTAL PORTFOLIO VALUE
        # -------------------------------------------------

        total = sum(
            holding.current_value
            for holding in request.holdings
        )

        if not np.isfinite(total) or total <= 0:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Portfolio value must be "
                    "positive and finite."
                ),
            )

        # -------------------------------------------------
        # STEP 2: GROUP HOLDINGS BY ASSET CLASS
        # -------------------------------------------------

        amounts = {
            asset: 0.0
            for asset in ASSETS
        }

        for holding in request.holdings:

            amounts[holding.asset_class] += (
                holding.current_value
            )

        current_weights = {
            asset: (
                amounts[asset] / total
            )
            for asset in ASSETS
        }

        # -------------------------------------------------
        # STEP 3: MAP USER RISK TOLERANCE
        # -------------------------------------------------

        risk_profile = RISK_MAP[
            request.risk_tolerance
        ]

        # -------------------------------------------------
        # STEP 4: VALIDATE MARKET DATA
        # -------------------------------------------------

        if market_data.empty:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Market data is unavailable."
                ),
            )

        missing_features = [
            column
            for column in MARKET_FEATURES
            if column not in market_data.columns
        ]

        if missing_features:
            raise HTTPException(
                status_code=503,
                detail={
                    "message": (
                        "Required market features "
                        "are missing."
                    ),
                    "missing_features": (
                        missing_features
                    ),
                },
            )

        # -------------------------------------------------
        # STEP 5: GET LATEST MARKET OBSERVATION
        # -------------------------------------------------

        row = market_data.iloc[-1]

        features = np.asarray(
            [
                row[column]
                for column in MARKET_FEATURES
            ],
            dtype=np.float32,
        )

        if not np.isfinite(features).all():
            raise HTTPException(
                status_code=503,
                detail=(
                    "Latest market features "
                    "contain invalid values."
                ),
            )

        # -------------------------------------------------
        # STEP 6: BUILD CURRENT WEIGHT VECTOR
        # -------------------------------------------------

        weights_vector = np.asarray(
            [
                current_weights[asset]
                for asset in ASSETS
            ],
            dtype=np.float32,
        )

        # -------------------------------------------------
        # STEP 7: BUILD 18-FEATURE PPO OBSERVATION
        # -------------------------------------------------

        observation = np.concatenate(
            [
                weights_vector,
                features,
                np.asarray(
                    [risk_profile],
                    dtype=np.float32,
                ),
            ]
        ).astype(np.float32)

        if observation.shape != (18,):
            raise HTTPException(
                status_code=500,
                detail=(
                    "Invalid PPO observation shape. "
                    "Expected 18 features."
                ),
            )

        if not np.isfinite(observation).all():
            raise HTTPException(
                status_code=500,
                detail=(
                    "PPO observation contains "
                    "invalid values."
                ),
            )

        # -------------------------------------------------
        # STEP 8: RUN PPO MODEL
        # -------------------------------------------------

        action, _ = model.predict(
            observation,
            deterministic=True,
        )

        # -------------------------------------------------
        # STEP 9: CONVERT ACTION TO ALLOCATION
        # -------------------------------------------------

        try:
            proposed_weights = (
                convert_action_to_weights(
                    action
                )
            )

        except ValueError as error:
            raise HTTPException(
                status_code=500,
                detail=str(error),
            ) from error

        target_weights = {
            asset: float(weight)
            for asset, weight in zip(
                ASSETS,
                proposed_weights,
            )
        }

        # -------------------------------------------------
        # STEP 10: PPO SENSITIVITY ANALYSIS
        # -------------------------------------------------

        # Use the SAME observation passed to PPO.
        # The sensitivity function changes selected
        # inputs and runs additional predictions.

        try:
            sensitivity = (
                analyze_model_sensitivity(
                    model=model,
                    observation=observation,
                )
            )

        except ValueError as error:
            raise HTTPException(
                status_code=500,
                detail=(
                    "PPO sensitivity analysis failed: "
                    f"{error}"
                ),
            ) from error

        # -------------------------------------------------
        # STEP 11: VERIFY SENSITIVITY BASELINE
        # -------------------------------------------------

        # Baseline weights from sensitivity analysis
        # should match the original PPO allocation.

        baseline_weights = (
            sensitivity["baseline_weights"]
        )

        for asset in ASSETS:

            difference = abs(
                baseline_weights[asset]
                - target_weights[asset]
            )

            if difference > 1e-4:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "PPO sensitivity baseline "
                        "does not match the original "
                        f"allocation for {asset}."
                    ),
                )

        # -------------------------------------------------
        # STEP 12: BUILD FINANCIAL INSIGHTS REQUEST
        # -------------------------------------------------

        insights_request = InsightsRequest(
            holdings=[
                {
                    "name": holding.name,
                    "asset_class": (
                        holding.asset_class
                    ),
                    "current_value": (
                        holding.current_value
                    ),
                }
                for holding in request.holdings
            ],

            target_weights=target_weights,

            horizon_years=(
                request.investment_horizon_years
            ),

            goal_amount=request.goal_amount,

            monthly_sip=request.monthly_sip,
        )

        # -------------------------------------------------
        # STEP 13: GENERATE FINANCIAL INSIGHTS
        # -------------------------------------------------

        insights = portfolio_insights(
            insights_request
        )

        # -------------------------------------------------
        # STEP 14: GENERATE DYNAMIC EXPLANATIONS
        # -------------------------------------------------

        explanations = create_explanations(
            current_weights=current_weights,
            proposed_weights=target_weights,
            insights=insights,
        )

        # -------------------------------------------------
        # STEP 15: GET MARKET DATA REFERENCE DATE
        # -------------------------------------------------

        latest_index = (
            market_data.index[-1]
        )

        market_date = (
            latest_index.isoformat()
            if isinstance(
                latest_index,
                pd.Timestamp,
            )
            else str(latest_index)
        )

        # -------------------------------------------------
        # STEP 16: FINAL API RESPONSE
        # -------------------------------------------------

        return {
            "status": "completed",

            "model_version": "PPO V2",

            "optimization_type": (
                "experimental_single_step_inference"
            ),

            "market_data_reference": (
                market_date
            ),

            "market_data_is_live": False,

            "risk_profile": float(
                risk_profile
            ),

            "risk_tolerance": (
                request.risk_tolerance
            ),

            "investment_horizon_years": (
                request.investment_horizon_years
            ),

            "portfolio_value": round(
                total,
                2,
            ),

            "current_weights": (
                current_weights
            ),

            "proposed_weights": (
                target_weights
            ),

            "insights": insights,

            "explanations": explanations,

            "model_sensitivity": (
                sensitivity
            ),

            "disclaimer": (
                "Experimental PPO V2 model output "
                "using the latest available local "
                "historical dataset row. "
                "Not a validated live investment "
                "recommendation. "
                "Future scenarios are illustrative. "
                "Sensitivity analysis shows model "
                "responses to controlled input "
                "changes, not causal explanations "
                "or evidence of future performance."
            ),
        }

    return router
