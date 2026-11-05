
"""
Portfolio Optimizer FastAPI Backend — PPO V2

Features:
- Loads trained PPO V2 model once
- Uses PortfolioEnvV2
- Runs simulations on reserved test data
- Supports different investor risk profiles
- Returns portfolio performance and allocation
- Includes estimated taxes and transaction fees
- Supports portfolio analysis and CSV/Excel uploads
- Supports goal planning, rebalancing and stress testing
- Supports personalized PPO optimization
- Supports simple and technical explanations
- Supports PPO sensitivity analysis through personalized.py
"""

import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from stable_baselines3 import PPO


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# PROJECT IMPORTS
# ---------------------------------------------------------

from RL.env_v2 import PortfolioEnvV2

from app.backend.portfolio import (
    router as portfolio_router,
)

from app.backend.portfolio_upload import (
    router as upload_router,
)

from app.backend.portfolio_insights import (
    router as insights_router,
)

from app.backend.personalized import (
    create_personalized_router,
)


# ---------------------------------------------------------
# MODEL AND DATA PATHS
# ---------------------------------------------------------

MODEL_PATH = (
    PROJECT_ROOT
    / "RL"
    / "models"
    / "ppo_portfolio_model_v2.zip"
)

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "processed_market_data_v2.parquet"
)


# ---------------------------------------------------------
# VERIFY REQUIRED FILES
# ---------------------------------------------------------

if not MODEL_PATH.is_file():
    raise FileNotFoundError(
        f"PPO V2 model not found: {MODEL_PATH}"
    )

if not DATA_PATH.is_file():
    raise FileNotFoundError(
        f"Processed market data not found: {DATA_PATH}"
    )


# ---------------------------------------------------------
# LOAD PPO V2 MODEL
# ---------------------------------------------------------

print("Loading PPO V2 model...")

model = PPO.load(
    str(MODEL_PATH),
    device="cpu",
)

print("PPO V2 model loaded successfully.")


# ---------------------------------------------------------
# LOAD MARKET DATA
# ---------------------------------------------------------

full_market_data = (
    pd.read_parquet(DATA_PATH)
    .sort_index()
)

if len(full_market_data) < 3:
    raise ValueError(
        "Market dataset must contain at least 3 rows."
    )

train_size = int(len(full_market_data) * 0.8)

market_data = (
    full_market_data
    .iloc[train_size:]
    .copy()
)

print("Total market rows:", len(full_market_data))
print("Reserved test rows:", len(market_data))


# ---------------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------------

app = FastAPI(
    title="Portfolio Optimizer API",
    description=(
        "PPO V2 portfolio optimization with historical "
        "backtesting, portfolio insights, explainability "
        "and model sensitivity analysis."
    ),
    version="2.2.0",
)


# ---------------------------------------------------------
# CORS CONFIGURATION
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# REGISTER API ROUTERS
# ---------------------------------------------------------

# POST /portfolio/analyze
app.include_router(
    portfolio_router
)

# POST /portfolio/upload
app.include_router(
    upload_router
)

# POST /portfolio/insights
app.include_router(
    insights_router
)

# POST /portfolio/optimize
# Includes explainability and sensitivity analysis
# when implemented in personalized.py.
app.include_router(
    create_personalized_router(
        model=model,
        market_data=full_market_data,
    )
)


# ---------------------------------------------------------
# SIMULATION REQUEST MODEL
# ---------------------------------------------------------

class SimulationRequest(BaseModel):

    risk_profile: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    initial_balance: float = Field(
        default=100000.0,
        gt=0,
    )


# ---------------------------------------------------------
# PERFORMANCE METRICS
# ---------------------------------------------------------

def calculate_sharpe_ratio(portfolio_values):

    values = np.asarray(
        portfolio_values,
        dtype=float,
    )

    if len(values) < 2:
        return 0.0

    if not np.isfinite(values).all():
        raise ValueError(
            "Portfolio values contain non-finite numbers."
        )

    if np.any(values[:-1] <= 0):
        raise ValueError(
            "Portfolio values must be positive "
            "when calculating returns."
        )

    returns = (
        np.diff(values)
        / values[:-1]
    )

    volatility = np.std(returns)

    if volatility < 1e-12:
        return 0.0

    # Match evaluation_v2.py:
    # 5% assumed annual risk-free rate.
    risk_free_daily = 0.05 / 252

    sharpe = (
        np.mean(
            returns - risk_free_daily
        )
        / volatility
        * np.sqrt(252)
    )

    return float(sharpe)


def calculate_max_drawdown(portfolio_values):

    values = np.asarray(
        portfolio_values,
        dtype=float,
    )

    if len(values) < 2:
        return 0.0

    if not np.isfinite(values).all():
        raise ValueError(
            "Portfolio values contain non-finite numbers."
        )

    peaks = np.maximum.accumulate(
        values
    )

    drawdowns = (
        values / peaks - 1.0
    )

    return float(
        np.min(drawdowns)
    )


# ---------------------------------------------------------
# RUN HISTORICAL SIMULATION
# ---------------------------------------------------------

def run_simulation(request: SimulationRequest):

    print(
        "\n===== PPO V2 SIMULATION STARTED ====="
    )

    print(
        "Risk profile:",
        request.risk_profile,
    )

    print(
        "Initial balance:",
        request.initial_balance,
    )

    # Use reserved out-of-sample test data.
    environment = PortfolioEnvV2(
        df=market_data.copy(),
        risk_profile=request.risk_profile,
        initial_balance=request.initial_balance,
    )

    observation, _ = environment.reset()

    portfolio_values = [
        float(environment.portfolio_value)
    ]

    rewards = []

    step_count = 0

    while True:

        action, _ = model.predict(
            observation,
            deterministic=True,
        )

        (
            observation,
            reward,
            terminated,
            truncated,
            _,
        ) = environment.step(action)

        rewards.append(
            float(reward)
        )

        portfolio_values.append(
            float(environment.portfolio_value)
        )

        step_count += 1

        if terminated or truncated:
            break

    # -----------------------------------------------------
    # FINAL ALLOCATION
    # -----------------------------------------------------

    allocation = {
        asset: round(
            float(weight),
            6,
        )
        for asset, weight in zip(
            environment.assets,
            environment.weights,
        )
    }

    # -----------------------------------------------------
    # PERFORMANCE
    # -----------------------------------------------------

    final_portfolio_value = float(
        environment.portfolio_value
    )

    total_return = (
        final_portfolio_value
        / request.initial_balance
        - 1.0
    )

    sharpe_ratio = calculate_sharpe_ratio(
        portfolio_values
    )

    max_drawdown = calculate_max_drawdown(
        portfolio_values
    )

    # -----------------------------------------------------
    # ESTIMATED TAXES AND FEES
    # -----------------------------------------------------

    total_tax = sum(
        float(item["tax_paid"])
        for item in environment.history
    )

    total_fees = sum(
        float(item["transaction_fee"])
        for item in environment.history
    )

    # -----------------------------------------------------
    # API RESPONSE
    # -----------------------------------------------------

    result = {
        "risk_profile": float(
            request.risk_profile
        ),

        "initial_balance": float(
            request.initial_balance
        ),

        "final_portfolio_value": round(
            final_portfolio_value,
            2,
        ),

        "total_return": round(
            float(total_return),
            6,
        ),

        "target_weights": allocation,

        "sharpe_ratio": round(
            sharpe_ratio,
            4,
        ),

        "max_drawdown": round(
            max_drawdown,
            4,
        ),

        "steps": int(
            step_count
        ),

        "portfolio_values": [
            round(float(value), 2)
            for value in portfolio_values
        ],

        "rewards": [
            round(float(reward), 6)
            for reward in rewards
        ],

        "estimated_tax_paid": round(
            total_tax,
            2,
        ),

        "transaction_fees": round(
            total_fees,
            2,
        ),

        "model_version": "PPO V2",

        "evaluation_type": (
            "Out-of-sample backtest"
        ),
    }

    print(
        "Final allocation:",
        allocation,
    )

    print(
        "Final value:",
        final_portfolio_value,
    )

    print(
        "Sharpe ratio:",
        sharpe_ratio,
    )

    print(
        "Maximum drawdown:",
        max_drawdown,
    )

    print(
        "Estimated tax:",
        total_tax,
    )

    print(
        "Transaction fees:",
        total_fees,
    )

    print(
        "===== SIMULATION FINISHED =====\n"
    )

    return result


# ---------------------------------------------------------
# SIMULATION ENDPOINT
# ---------------------------------------------------------

@app.post("/simulate")
def simulate_portfolio(
    request: SimulationRequest,
):

    try:
        return run_simulation(
            request
        )

    except Exception as error:

        print(
            "\n========== SIMULATION ERROR =========="
        )

        print(
            "Error type:",
            type(error).__name__,
        )

        print(
            "Error message:",
            str(error),
        )

        traceback.print_exc()

        print(
            "======================================\n"
        )

        raise


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/")
def root():

    return {
        "status": "ok",
        "message": (
            "Portfolio Optimizer PPO V2 API is running"
        ),
        "model_version": "PPO V2",
        "api_version": "2.2.0",
        "features": [
            "historical_simulation",
            "portfolio_analysis",
            "portfolio_upload",
            "portfolio_insights",
            "personalized_optimization",
            "simple_explanations",
            "technical_explanations",
            "model_sensitivity",
        ],
    }
