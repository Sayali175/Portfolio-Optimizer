import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

class PortfolioEnv(gym.Env):
    """
    Custom Portfolio Optimization Environment compliant with Gymnasium.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        df: pd.DataFrame,
        risk_profile: float = 0.5,
        transaction_cost: float = 0.001,  # 10 bps turnover fee
        initial_balance: float = 100000.0,
    ):
        super(PortfolioEnv, self).__init__()

        self.df = df.reset_index(drop=True)
        self.risk_profile = float(risk_profile)  # 0.0 (Low), 0.5 (Medium), 1.0 (High)
        self.transaction_cost = transaction_cost
        self.initial_balance = initial_balance

        self.assets = ["equity", "debt", "hybrid", "liquid"]
        self.num_assets = len(self.assets)

        # 4 weights + 4 returns + 4 vols + 5 nifty indicators + 1 risk scalar = 18
        obs_dim = (self.num_assets * 3) + 5 + 1
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )

        # Continuous target weights logits
        self.action_space = spaces.Box(
            low=-5.0, high=5.0, shape=(self.num_assets,), dtype=np.float32
        )

        self._reset_state()

    def _reset_state(self):
        self.current_step = 0
        self.max_steps = len(self.df) - 1
        self.portfolio_value = self.initial_balance
        # Start equal-weighted across the 4 assets
        self.weights = np.ones(self.num_assets, dtype=np.float32) / self.num_assets
        self.history = []

    def _get_observation(self):
        row = self.df.iloc[self.current_step]

        asset_returns = np.array([row[f"{a}_return"] for a in self.assets], dtype=np.float32)
        asset_vols = np.array([row[f"{a}_vol_30d"] for a in self.assets], dtype=np.float32)
        
        nifty_features = np.array([
            row["nifty_return"],
            row["nifty_vol_30d"],
            row["nifty_rsi_14"],
            row["nifty_sma_ratio"],
            row["nifty_macd_diff"],
        ], dtype=np.float32)

        risk_scalar = np.array([self.risk_profile], dtype=np.float32)

        obs = np.concatenate([
            self.weights,
            asset_returns,
            asset_vols,
            nifty_features,
            risk_scalar,
        ])
        return obs.astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._reset_state()
        return self._get_observation(), {}

    def step(self, action):
        # Softmax allocation to ensure weights are non-negative and sum to 1.0
        exp_action = np.exp(action - np.max(action))
        target_weights = exp_action / np.sum(exp_action)

        row = self.df.iloc[self.current_step]
        realized_asset_returns = np.array([row[f"{a}_return"] for a in self.assets], dtype=np.float32)

        # Portfolio return before costs
        gross_return = np.sum(target_weights * realized_asset_returns)

        # Turnover cost penalty
        turnover = np.sum(np.abs(target_weights - self.weights))
        rebalance_cost = turnover * self.transaction_cost

        net_return = gross_return - rebalance_cost

        # Update portfolio value
        self.portfolio_value *= (1.0 + net_return)
        self.weights = target_weights

        # Volatility/Risk penalty based on risk profile
        # Lower risk profile = higher penalty for volatile assets (e.g., equity)
        portfolio_vol = np.sum(target_weights * np.array([row[f"{a}_vol_30d"] for a in self.assets]))
        risk_aversion = (1.5 - self.risk_profile) * 2.0  # Scalar factor
        risk_penalty = risk_aversion * (portfolio_vol ** 2)

        # Net reward for PPO
        reward = float(net_return * 100.0 - risk_penalty)

        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        truncated = False

        self.history.append({
            "step": self.current_step,
            "portfolio_value": self.portfolio_value,
            "weights": self.weights.copy(),
            "reward": reward,
        })

        obs = self._get_observation() if not terminated else np.zeros(self.observation_space.shape, dtype=np.float32)
        return obs, reward, terminated, truncated, {}