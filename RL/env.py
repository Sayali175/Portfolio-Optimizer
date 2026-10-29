import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd


class PortfolioEnv(gym.Env):
    """
    Tax-Aware Portfolio Optimization Environment compliant with Gymnasium.
    Integrates Indian Short-Term Capital Gains (STCG) tax and turnover costs
    to avoid unprofitable, high-frequency rebalancing.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        df: pd.DataFrame,
        risk_profile: float = 0.5,  # 0.0 (Low), 0.5 (Medium), 1.0 (High)
        transaction_cost: float = 0.001,  # 10 bps brokerage/STT
        rebalance_threshold: float = 0.03,  # 3% minimum weight shift deadband
        initial_balance: float = 100000.0,
    ):
        super(PortfolioEnv, self).__init__()

        self.df = df.reset_index(drop=True)
        self.risk_profile = float(risk_profile)
        self.transaction_cost = transaction_cost
        self.rebalance_threshold = rebalance_threshold
        self.initial_balance = initial_balance

        self.assets = ["equity", "debt", "hybrid", "liquid"]
        self.num_assets = len(self.assets)

        # Indian Short-Term Capital Gains (STCG) tax rates:
        # Equity & Equity-Oriented Hybrid: 20%
        # Debt & Liquid: Taxed at slab rate (assuming 30% tax bracket)
        self.stcg_rates = np.array([0.20, 0.30, 0.20, 0.30], dtype=np.float32)

        # Observation dimensions:
        # 4 weights + 4 returns + 4 volatilities + 5 NIFTY indicators + 1 risk scalar = 18
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

        # Initial equal weight across the 4 asset categories
        self.weights = np.ones(self.num_assets, dtype=np.float32) / self.num_assets

        # Track monetary allocation and cost basis per asset category
        self.asset_capital = self.initial_balance * self.weights.copy()
        self.cost_basis = self.asset_capital.copy()

        self.history = []

    def _get_observation(self):
        row = self.df.iloc[self.current_step]

        asset_returns = np.array(
            [row[f"{a}_return"] for a in self.assets], dtype=np.float32
        )
        asset_vols = np.array(
            [row[f"{a}_vol_30d"] for a in self.assets], dtype=np.float32
        )

        nifty_features = np.array(
            [
                row["nifty_return"],
                row["nifty_vol_30d"],
                row["nifty_rsi_14"],
                row["nifty_sma_ratio"],
                row["nifty_macd_diff"],
            ],
            dtype=np.float32,
        )

        risk_scalar = np.array([self.risk_profile], dtype=np.float32)

        obs = np.concatenate(
            [
                self.weights,
                asset_returns,
                asset_vols,
                nifty_features,
                risk_scalar,
            ]
        )
        return obs.astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._reset_state()
        return self._get_observation(), {}

    def step(self, action):
        # 1. Softmax allocation ensures weights are non-negative and sum to 1.0
        exp_action = np.exp(action - np.max(action))
        proposed_weights = exp_action / np.sum(exp_action)

        # 2. Deadband threshold check:
        # If portfolio rebalance shift is lower than threshold, do not rebalance to save taxes
        weight_shift = np.sum(np.abs(proposed_weights - self.weights))
        if weight_shift < self.rebalance_threshold:
            target_weights = self.weights.copy()
            turnover = 0.0
        else:
            target_weights = proposed_weights
            turnover = weight_shift

        row = self.df.iloc[self.current_step]
        realized_asset_returns = np.array(
            [row[f"{a}_return"] for a in self.assets], dtype=np.float32
        )

        # 3. Mark-to-market capital growth before rebalancing
        self.asset_capital = self.asset_capital * (1.0 + realized_asset_returns)
        pre_rebalance_total = float(np.sum(self.asset_capital))

        # 4. Compute Short-Term Capital Gains (STCG) on trimmed/sold portions
        total_tax_paid = 0.0
        new_target_capital = pre_rebalance_total * target_weights

        for i in range(self.num_assets):
            if new_target_capital[i] < self.asset_capital[i]:
                # Asset category is being sold
                redeemed_amount = self.asset_capital[i] - new_target_capital[i]

                # Proportion of capital that is taxable profit
                profit_margin = max(
                    0.0,
                    (self.asset_capital[i] - self.cost_basis[i])
                    / (self.asset_capital[i] + 1e-8),
                )
                realized_profit = redeemed_amount * profit_margin

                # Deduct Indian STCG rate on positive short term gains
                tax = realized_profit * self.stcg_rates[i]
                total_tax_paid += tax

        # 5. Apply transaction fees and tax deductions
        rebalance_cost = (turnover * pre_rebalance_total) * self.transaction_cost
        post_tax_total = pre_rebalance_total - rebalance_cost - total_tax_paid

        # Update balance and cost basis
        self.portfolio_value = max(post_tax_total, 1.0)
        self.weights = target_weights
        self.asset_capital = self.portfolio_value * self.weights
        self.cost_basis = self.asset_capital.copy()

        # 6. Reward function: Post-tax return penalized for risk
        net_return = (self.portfolio_value - pre_rebalance_total) / pre_rebalance_total
        portfolio_vol = np.sum(
            target_weights * np.array([row[f"{a}_vol_30d"] for a in self.assets])
        )
        risk_aversion = (1.5 - self.risk_profile) * 2.0
        risk_penalty = risk_aversion * (portfolio_vol**2)

        # Scale return and deduct risk penalty
        reward = float((net_return * 100.0) - risk_penalty)

        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        truncated = False

        self.history.append(
            {
                "step": self.current_step,
                "portfolio_value": self.portfolio_value,
                "weights": self.weights.copy(),
                "tax_paid": total_tax_paid,
                "reward": reward,
            }
        )

        obs = (
            self._get_observation()
            if not terminated
            else np.zeros(self.observation_space.shape, dtype=np.float32)
        )
        return obs, reward, terminated, truncated, {}