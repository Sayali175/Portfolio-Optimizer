
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from stable_baselines3 import PPO
from RL.env_v2 import PortfolioEnvV2


DATA_PATH = "data/processed/processed_market_data_v2.parquet"
MODEL_PATH = "RL/models/ppo_portfolio_model_v2.zip"


def metrics(values):
    values = np.asarray(values, dtype=float)
    returns = values[1:] / values[:-1] - 1.0

    total_return = (values[-1] / values[0] - 1) * 100
    annual_vol = np.std(returns) * np.sqrt(252) * 100

    risk_free_daily = 0.05 / 252
    sharpe = (
        np.mean(returns - risk_free_daily)
        / (np.std(returns) + 1e-8)
        * np.sqrt(252)
    )

    peak = np.maximum.accumulate(values)
    max_dd = np.min(values / peak - 1) * 100

    return {
        "Return (%)": round(total_return, 2),
        "Volatility (%)": round(annual_vol, 2),
        "Sharpe": round(float(sharpe), 3),
        "Max Drawdown (%)": round(float(max_dd), 2),
        "Final Value": round(float(values[-1]), 2),
    }


def benchmark_values(test_df, weights):
    assets = ["equity", "debt", "hybrid", "liquid"]

    # The environment starts at row 0 and applies
    # returns from rows 1 through the final row.
    returns = test_df[
        [f"{a}_return" for a in assets]
    ].iloc[1:].to_numpy()

    # Fixed-weight, daily-rebalanced theoretical benchmark.
    daily = returns @ np.asarray(weights, dtype=float)

    return np.concatenate([
        [100000.0],
        100000.0 * np.cumprod(1.0 + daily)
    ])


def main():
    df = pd.read_parquet(DATA_PATH).sort_index()

    split = int(len(df) * 0.8)
    test_df = df.iloc[split:].copy()

    model = PPO.load(MODEL_PATH, device="cpu")

    os.makedirs("docs", exist_ok=True)

    for risk in [0.1, 0.5, 0.9]:
        env = PortfolioEnvV2(
            df=test_df,
            risk_profile=risk,
            initial_balance=100000.0,
        )

        obs, _ = env.reset()
        values = [env.portfolio_value]

        done = False

        while not done:
            action, _ = model.predict(
                obs, deterministic=True
            )

            obs, reward, terminated, truncated, _ = env.step(action)

            values.append(env.portfolio_value)
            done = terminated or truncated

        values = np.asarray(values)

        results = {
            "PPO V2": metrics(values),
            "Equal Weight": metrics(
                benchmark_values(test_df, [0.25] * 4)
            ),
            "60/40 Equity-Debt": metrics(
                benchmark_values(test_df, [0.6, 0.4, 0, 0])
            ),
            "NIFTY 50": metrics(
                np.concatenate([
                    [100000.0],
                    100000.0 * np.cumprod(
                        1.0 + test_df["nifty_return"].iloc[1:].to_numpy()
                    )
                ])
            ),
        }

        report = pd.DataFrame(results).T

        print(f"\n===== RISK PROFILE {risk} =====")
        print(report.to_string())

        report.to_csv(f"docs/evaluation_v2_risk_{risk}.csv")

        plt.figure(figsize=(10, 5))
        plt.plot(values, label="PPO V2")

        plt.plot(
            benchmark_values(test_df, [0.25] * 4),
            label="Equal Weight",
        )

        plt.plot(
            benchmark_values(test_df, [0.6, 0.4, 0, 0]),
            label="60/40",
        )

        plt.title(f"Out-of-Sample Performance - Risk {risk}")
        plt.xlabel("Trading Days")
        plt.ylabel("Portfolio Value (INR)")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"docs/evaluation_v2_risk_{risk}.png")
        plt.close()

        print(
            "Final PPO allocation:",
            dict(zip(
                env.assets,
                np.round(env.weights, 4)
            ))
        )

        print(
            "Estimated tax:",
            round(sum(x["tax_paid"] for x in env.history), 2)
        )

        print(
            "Trading fees:",
            round(sum(x["transaction_fee"] for x in env.history), 2)
        )

    print("\nEVALUATION V2 COMPLETE")


if __name__ == "__main__":
    main()
