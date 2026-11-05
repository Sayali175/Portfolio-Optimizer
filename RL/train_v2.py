
import os
import random
import numpy as np
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

from RL.env_v2 import PortfolioEnvV2


DATA_PATH = "data/processed/processed_market_data_v2.parquet"
MODEL_PATH = "RL/models/ppo_portfolio_model_v2"
RISK_PROFILES = [0.1, 0.3, 0.5, 0.7, 0.9]


class RandomRiskPortfolioEnv(PortfolioEnvV2):
    """Select a different risk profile for each training episode."""

    def reset(self, seed=None, options=None):
        self.risk_profile = random.choice(RISK_PROFILES)
        return super().reset(seed=seed, options=options)


def main():
    random.seed(42)
    np.random.seed(42)

    df = pd.read_parquet(DATA_PATH).sort_index()

    split = int(len(df) * 0.8)
    train_df = df.iloc[:split].copy()

    print("Total rows:", len(df))
    print("Training rows:", len(train_df))
    print("Reserved test rows:", len(df) - split)

    env = Monitor(
        RandomRiskPortfolioEnv(
            df=train_df,
            risk_profile=0.5,
            initial_balance=100000.0,
        )
    )

    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=0.0003,
        n_steps=1024,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.01,
        verbose=1,
        device="cpu",
        seed=42,
    )

    print("Starting PPO V2 training...")

    model.learn(total_timesteps=30000)

    os.makedirs("RL/models", exist_ok=True)
    model.save(MODEL_PATH)

    print("TRAINING COMPLETE")
    print("Saved:", MODEL_PATH + ".zip")


if __name__ == "__main__":
    main()
