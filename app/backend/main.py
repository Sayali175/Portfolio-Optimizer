"""
Portfolio Optimizer FastAPI Backend

Phase 2:
- Load trained PPO model once at startup
- Run portfolio simulations through PortfolioEnv
- Expose POST /simulate
- Calculate Sharpe Ratio and Maximum Drawdown
"""

import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field
from stable_baselines3 import PPO


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(PROJECT_ROOT))

from RL.env import PortfolioEnv


MODEL_PATH = (
    PROJECT_ROOT
    / "RL"
    / "models"
    / "ppo_portfolio_model.zip"
)

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "processed_market_data.parquet"
)


# ---------------------------------------------------------
# LOAD MODEL ONCE
# ---------------------------------------------------------

print("Loading PPO model...")

model = PPO.load(
    str(MODEL_PATH),
    device="cpu"
)

print("PPO model loaded successfully.")


# ---------------------------------------------------------
# LOAD MARKET DATA
# ---------------------------------------------------------

market_data = pd.read_parquet(DATA_PATH)

print(f"Market data loaded: {len(market_data)} rows")


# ---------------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------------

app = FastAPI(
    title="Portfolio Optimizer API",
    description="AI-powered portfolio optimization backend",
    version="2.0.0",
)


# ---------------------------------------------------------
# REQUEST MODEL
# ---------------------------------------------------------

class SimulationRequest(BaseModel):

    risk_profile: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Risk profile from 0 (low risk) to 1 (high risk)",
    )

    initial_balance: float = Field(
        default=100000.0,
        gt=0,
        description="Starting portfolio value",
    )


# ---------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------

def calculate_sharpe_ratio(portfolio_values):

    portfolio_values = np.array(
        portfolio_values,
        dtype=float
    )

    if len(portfolio_values) < 2:
        return 0.0

    returns = (
        np.diff(portfolio_values)
        / portfolio_values[:-1]
    )

    if np.std(returns) == 0:
        return 0.0

    sharpe_ratio = (
        np.mean(returns)
        / np.std(returns)
        * np.sqrt(252)
    )

    return float(sharpe_ratio)


# ---------------------------------------------------------
# MAXIMUM DRAWDOWN
# ---------------------------------------------------------

def calculate_max_drawdown(portfolio_values):

    portfolio_values = np.array(
        portfolio_values,
        dtype=float
    )

    if len(portfolio_values) == 0:
        return 0.0

    running_max = np.maximum.accumulate(
        portfolio_values
    )

    drawdowns = (
        portfolio_values - running_max
    ) / running_max

    max_drawdown = np.min(drawdowns)

    return float(max_drawdown)


# ---------------------------------------------------------
# SIMULATION FUNCTION
# ---------------------------------------------------------

def run_simulation(request: SimulationRequest):

    print("\n===== SIMULATION STARTED =====")
    print("Risk profile:", request.risk_profile)
    print("Initial balance:", request.initial_balance)

    # -----------------------------------------------------
    # CREATE ENVIRONMENT
    # -----------------------------------------------------

    print("Creating PortfolioEnv...")

    environment = PortfolioEnv(
        df=market_data.copy(),
        risk_profile=request.risk_profile,
        initial_balance=request.initial_balance,
    )

    print("PortfolioEnv created successfully.")

    # -----------------------------------------------------
    # RESET ENVIRONMENT
    # -----------------------------------------------------

    print("Resetting environment...")

    observation, _ = environment.reset()

    print(
        "Environment reset successfully."
    )

    print(
        "Observation shape:",
        observation.shape
    )

    # -----------------------------------------------------
    # INITIAL PORTFOLIO VALUE
    # -----------------------------------------------------

    portfolio_values = [
        environment.portfolio_value
    ]

    rewards = []

    step_count = 0

    # -----------------------------------------------------
    # RUN PPO THROUGH ENVIRONMENT
    # -----------------------------------------------------

    print("Starting PPO simulation...")

    while True:

        # Get action from trained PPO model
        action, _state = model.predict(
            observation,
            deterministic=True
        )

        (
            observation,
            reward,
            terminated,
            truncated,
            _info,
        ) = environment.step(action)

        rewards.append(
            float(reward)
        )

        portfolio_values.append(
            float(environment.portfolio_value)
        )

        step_count += 1

        # Stop when environment reaches the end
        if terminated or truncated:
            break

    print(
        "Simulation completed."
    )

    print(
        "Total simulation steps:",
        step_count
    )

    # -----------------------------------------------------
    # FINAL PORTFOLIO ALLOCATION
    # -----------------------------------------------------

    final_weights = environment.weights

    allocation = {
        asset: round(float(weight), 6)
        for asset, weight in zip(
            environment.assets,
            final_weights
        )
    }

    print(
        "Final allocation:",
        allocation
    )

    # -----------------------------------------------------
    # PERFORMANCE METRICS
    # -----------------------------------------------------

    print("Calculating performance metrics...")

    sharpe_ratio = calculate_sharpe_ratio(
        portfolio_values
    )

    max_drawdown = calculate_max_drawdown(
        portfolio_values
    )

    print(
        "Sharpe Ratio:",
        sharpe_ratio
    )

    print(
        "Maximum Drawdown:",
        max_drawdown
    )

    # -----------------------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------------------

    result = {

        "risk_profile": request.risk_profile,

        "initial_balance": request.initial_balance,

        "final_portfolio_value": round(
            float(environment.portfolio_value),
            2
        ),

        "total_return": round(
            (
                environment.portfolio_value
                / request.initial_balance
                - 1
            ),
            6
        ),

        "target_weights": allocation,

        "sharpe_ratio": round(
            sharpe_ratio,
            4
        ),

        "max_drawdown": round(
            max_drawdown,
            4
        ),

        "steps": step_count,

        "portfolio_values": [
            round(float(value), 2)
            for value in portfolio_values
        ],

        "rewards": [
            round(float(reward), 6)
            for reward in rewards
        ],
    }

    print("===== SIMULATION FINISHED =====\n")

    return result


# ---------------------------------------------------------
# SIMULATION ENDPOINT
# ---------------------------------------------------------

@app.post("/simulate")
def simulate_portfolio(
    request: SimulationRequest
):

    try:

        return run_simulation(request)

    except Exception as error:

        print(
            "\n========== SIMULATION ERROR =========="
        )

        print(
            "Error type:",
            type(error).__name__
        )

        print(
            "Error message:",
            str(error)
        )

        print(
            "\nFull traceback:"
        )

        traceback.print_exc()

        print(
            "======================================\n"
        )

        # Re-raise the error so FastAPI returns 500
        raise


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/")
def root():

    return {
        "status": "ok",
        "message": "Portfolio Optimizer API is running",
    }