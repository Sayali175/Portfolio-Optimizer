
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd


class PortfolioEnvV2(gym.Env):
    """
    Experimental tax-aware portfolio environment.

    Decision: use information through day t.
    Outcome: apply investment returns from day t+1.

    Taxes are simplified estimates, not a complete Indian tax engine.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        df: pd.DataFrame,
        risk_profile: float = 0.5,
        transaction_cost: float = 0.001,
        rebalance_threshold: float = 0.03,
        initial_balance: float = 100000.0,
    ):
        super().__init__()

        if len(df) < 2:
            raise ValueError("At least two market rows are required.")

        if not 0 <= risk_profile <= 1:
            raise ValueError("Risk profile must be between 0 and 1.")

        if initial_balance <= 0:
            raise ValueError("Initial balance must be positive.")

        if transaction_cost < 0 or rebalance_threshold < 0:
            raise ValueError("Costs and threshold cannot be negative.")

        self.df = df.reset_index(drop=True)
        self.risk_profile = float(risk_profile)
        self.transaction_cost = float(transaction_cost)
        self.rebalance_threshold = float(rebalance_threshold)
        self.initial_balance = float(initial_balance)

        self.assets = ["equity", "debt", "hybrid", "liquid"]
        self.num_assets = len(self.assets)

        # Simplified assumed tax rates, not verified legal tax rules.
        self.stcg_rates = np.array(
            [0.20, 0.30, 0.20, 0.30], dtype=np.float64
        )

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(18,),
            dtype=np.float32,
        )

        self.action_space = spaces.Box(
            low=-5.0,
            high=5.0,
            shape=(4,),
            dtype=np.float32,
        )

        self._reset_state()

    def _reset_state(self):
        self.current_step = 0
        self.max_steps = len(self.df) - 1

        self.portfolio_value = self.initial_balance

        self.weights = np.ones(4, dtype=np.float64) / 4.0
        self.asset_capital = self.weights * self.initial_balance

        # Remaining invested purchase cost per asset.
        self.cost_basis = self.asset_capital.copy()

        self.history = []

    def _get_observation(self):
        row = self.df.iloc[self.current_step]

        asset_returns = np.array(
            [row[f"{a}_return"] for a in self.assets],
            dtype=np.float32,
        )

        asset_vols = np.array(
            [row[f"{a}_vol_30d"] for a in self.assets],
            dtype=np.float32,
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

        return np.concatenate(
            [
                self.weights.astype(np.float32),
                asset_returns,
                asset_vols,
                nifty_features,
                np.array([self.risk_profile], dtype=np.float32),
            ]
        ).astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._reset_state()
        return self._get_observation(), {}

    def step(self, action):
        if self.current_step >= self.max_steps:
            raise RuntimeError("Episode has already ended.")

        action = np.asarray(action, dtype=np.float64)

        if action.shape != (4,) or not np.isfinite(action).all():
            raise ValueError("Action must contain four finite numbers.")

        action = np.clip(action, -5.0, 5.0)

        exp_action = np.exp(action - np.max(action))
        proposed_weights = exp_action / exp_action.sum()

        starting_value = float(self.portfolio_value)

        weight_shift = np.sum(
            np.abs(proposed_weights - self.weights)
        )

        tax_paid = 0.0
        transaction_fee = 0.0

        if weight_shift >= self.rebalance_threshold:
            # Estimate taxes and fees, then solve for the
            # investable post-cost balance.
            available = starting_value

            for _ in range(30):
                target_capital = available * proposed_weights
                sales = np.maximum(
                    self.asset_capital - target_capital, 0.0
                )

                profit_fraction = np.maximum(
                    1.0 - self.cost_basis /
                    np.maximum(self.asset_capital, 1e-12),
                    0.0,
                )

                estimated_tax = float(
                    np.sum(sales * profit_fraction * self.stcg_rates)
                )

                # Approximate fees on total traded notional.
                trades = np.abs(target_capital - self.asset_capital)
                estimated_fee = float(
                    trades.sum() * self.transaction_cost
                )

                new_available = max(
                    starting_value - estimated_tax - estimated_fee,
                    1e-8,
                )

                if abs(new_available - available) < 1e-7:
                    available = new_available
                    break

                available = new_available

            target_capital = available * proposed_weights

            sales = np.maximum(
                self.asset_capital - target_capital, 0.0
            )

            buys = np.maximum(
                target_capital - self.asset_capital, 0.0
            )

            profit_fraction = np.maximum(
                1.0 - self.cost_basis /
                np.maximum(self.asset_capital, 1e-12),
                0.0,
            )

            tax_paid = float(
                np.sum(sales * profit_fraction * self.stcg_rates)
            )

            transaction_fee = float(
                np.abs(target_capital - self.asset_capital).sum()
                * self.transaction_cost
            )

            # Preserve remaining purchase costs after sales.
            sold_fraction = sales / np.maximum(
                self.asset_capital, 1e-12
            )

            self.cost_basis = (
                self.cost_basis * (1.0 - sold_fraction) + buys
            )

            # Small numerical adjustment for final costs.
            post_cost_value = max(
                starting_value - tax_paid - transaction_fee,
                1e-8,
            )

            self.asset_capital = (
                post_cost_value * proposed_weights
            )

        # The action is chosen using day t information.
        # The investment outcome uses day t+1 returns.
        next_row = self.df.iloc[self.current_step + 1]

        next_returns = np.array(
            [next_row[f"{a}_return"] for a in self.assets],
            dtype=np.float64,
        )

        if not np.isfinite(next_returns).all():
            raise ValueError("Non-finite returns detected.")

        if np.any(next_returns <= -1.0):
            raise ValueError("Invalid asset return <= -100%.")

        self.asset_capital *= (1.0 + next_returns)

        self.portfolio_value = float(self.asset_capital.sum())

        # Actual holdings drift with market movements.
        self.weights = (
            self.asset_capital / self.portfolio_value
        )

        # Actual net daily portfolio return, including costs.
        net_return = (
            self.portfolio_value / starting_value
        ) - 1.0

        next_vols = np.array(
            [
                next_row[f"{a}_vol_30d"]
                for a in self.assets
            ],
            dtype=np.float64,
        )

        portfolio_vol = float(
            np.sum(self.weights * next_vols)
        )

        risk_aversion = (1.5 - self.risk_profile) * 2.0
        risk_penalty = risk_aversion * (portfolio_vol ** 2)

        reward = float(
            net_return * 100.0 - risk_penalty
        )

        self.current_step += 1

        terminated = self.current_step >= self.max_steps
        truncated = False

        self.history.append(
            {
                "step": self.current_step,
                "portfolio_value": self.portfolio_value,
                "weights": self.weights.copy(),
                "tax_paid": tax_paid,
                "transaction_fee": transaction_fee,
                "net_return": net_return,
                "reward": reward,
            }
        )

        observation = (
            np.zeros(18, dtype=np.float32)
            if terminated
            else self._get_observation()
        )

        return observation, reward, terminated, truncated, {}
