import pandas as pd
from stable_baselines3.common.env_checker import check_env
from RL.env import PortfolioEnv

df = pd.read_parquet("data/processed/processed_market_data.parquet")
env = PortfolioEnv(df=df, risk_profile=0.5)

# Gymnasium compatibility check
check_env(env)
print("Gymnasium environment check passed successfully!")

obs, _ = env.reset()
print(f"Observation Shape: {obs.shape}")
print(f"Action Space: {env.action_space}")