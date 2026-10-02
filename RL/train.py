import os
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from RL.env import PortfolioEnv

# Paths
DATA_PATH = "data/processed/processed_market_data.parquet"
MODEL_DIR = "RL/models"
MODEL_PATH = os.path.join(MODEL_DIR, "ppo_portfolio_model")

def train():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Processed data file not found at {DATA_PATH}")

    df = pd.read_parquet(DATA_PATH)
    print(f"Loaded dataset: {len(df)} total rows.")

    # 80/20 train/test split chronologically
    train_size = int(len(df) * 0.8)
    train_df = df.iloc[:train_size].copy()
    test_df = df.iloc[train_size:].copy()
    print(f"Train split size: {len(train_df)} rows | Out-of-sample split size: {len(test_df)} rows")

    # Instantiate the training environment (default medium risk: 0.5)
    env = PortfolioEnv(df=train_df, risk_profile=0.5)

    # Initialize PPO Agent with PyTorch MLP policy
    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,         # Encourages exploration across asset classes
        verbose=1,
        tensorboard_log="./tensorboard_logs/",
    )

    print("\nStarting PPO model training...")
    total_timesteps = 100_000
    model.learn(total_timesteps=total_timesteps)

    # Save final model
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save(MODEL_PATH)
    print(f"\nModel training complete! Saved to: {MODEL_PATH}.zip")

if __name__ == "__main__":
    train()