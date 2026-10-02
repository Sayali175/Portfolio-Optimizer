import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from RL.env import PortfolioEnv

DATA_PATH = "data/processed/processed_market_data.parquet"
MODEL_PATH = "RL/models/ppo_portfolio_model.zip"
REPORT_DIR = "docs"
os.makedirs(REPORT_DIR, exist_ok=True)


def calculate_metrics(portfolio_values: np.ndarray, daily_returns: np.ndarray):
    """Compute financial summary metrics."""
    total_return = (portfolio_values[-1] / portfolio_values[0]) - 1.0
    mean_return = np.mean(daily_returns)
    volatility = np.std(daily_returns) * np.sqrt(252)

    # Annualized Sharpe Ratio (assuming 5% risk-free rate)
    rf_daily = 0.05 / 252
    excess_returns = daily_returns - rf_daily
    sharpe_ratio = (
        (np.mean(excess_returns) / (np.std(excess_returns) + 1e-8)) * np.sqrt(252)
    )

    # Maximum Drawdown (MDD)
    peak = np.maximum.accumulate(portfolio_values)
    drawdowns = (portfolio_values - peak) / peak
    max_drawdown = np.min(drawdowns)

    return {
        "Total Return (%)": total_return * 100.0,
        "Annualized Vol (%)": volatility * 100.0,
        "Sharpe Ratio": sharpe_ratio,
        "Max Drawdown (%)": max_drawdown * 100.0,
    }


def evaluate():
    if not os.path.exists(DATA_PATH) or not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Processed dataset or trained PPO model is missing.")

    df = pd.read_parquet(DATA_PATH)
    train_size = int(len(df) * 0.8)
    test_df = df.iloc[train_size:].copy().reset_index(drop=True)

    print(f"Evaluating on {len(test_df)} out-of-sample trading days...")

    # Load trained agent
    model = PPO.load(MODEL_PATH)

    # 1. Simulate PPO Agent
    env = PortfolioEnv(df=test_df, risk_profile=0.5)
    obs, _ = env.reset()
    done = False

    ppo_values = [env.portfolio_value]
    ppo_weights = []

    while not done:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        ppo_values.append(env.portfolio_value)
        ppo_weights.append(env.weights)

    ppo_values = np.array(ppo_values)
    ppo_returns = np.diff(ppo_values) / ppo_values[:-1]

    # 2. Simulate Equal Weight (25% each)
    eq_returns = (
        0.25 * test_df["equity_return"]
        + 0.25 * test_df["debt_return"]
        + 0.25 * test_df["hybrid_return"]
        + 0.25 * test_df["liquid_return"]
    ).to_numpy()
    eq_values = 100000.0 * np.cumprod(1.0 + eq_returns)
    eq_values = np.insert(eq_values, 0, 100000.0)

    # 3. Simulate 60/40 Equity-Debt Benchmark
    sixty_forty_returns = (
        0.60 * test_df["equity_return"] + 0.40 * test_df["debt_return"]
    ).to_numpy()
    sixty_forty_values = 100000.0 * np.cumprod(1.0 + sixty_forty_returns)
    sixty_forty_values = np.insert(sixty_forty_values, 0, 100000.0)

    # 4. Simulate Pure NIFTY 50 Benchmark
    nifty_returns = test_df["nifty_return"].to_numpy()
    nifty_values = 100000.0 * np.cumprod(1.0 + nifty_returns)
    nifty_values = np.insert(nifty_values, 0, 100000.0)

    # Calculate metrics
    results = {
        "PPO Agent": calculate_metrics(ppo_values, ppo_returns),
        "Equal Weight (25/25/25/25)": calculate_metrics(eq_values, eq_returns),
        "60/40 Strategy": calculate_metrics(sixty_forty_values, sixty_forty_returns),
        "NIFTY 50": calculate_metrics(nifty_values, nifty_returns),
    }

    metrics_df = pd.DataFrame(results).T
    print("\n=== Out-of-Sample Performance Summary ===")
    print(metrics_df.round(2))

    # Save comparative metrics
    metrics_df.to_csv(os.path.join(REPORT_DIR, "backtest_metrics.csv"))

    # Plot cumulative returns
    plt.figure(figsize=(10, 6))
    plt.plot(ppo_values, label="PPO Dynamic Agent", color="blue", linewidth=2)
    plt.plot(eq_values, label="Equal Weight", color="green", linestyle="--")
    plt.plot(sixty_forty_values, label="60/40 Equity-Debt", color="orange", linestyle="--")
    plt.plot(nifty_values, label="NIFTY 50 Benchmark", color="red", linestyle=":")
    plt.title("Out-of-Sample Portfolio Growth Comparison")
    plt.xlabel("Trading Days")
    plt.ylabel("Portfolio Value (INR)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    chart_path = os.path.join(REPORT_DIR, "backtest_growth_chart.png")
    plt.savefig(chart_path)
    print(f"\nSaved performance plot to {chart_path}")


if __name__ == "__main__":
    evaluate()