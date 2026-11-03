
import unittest
import numpy as np
import pandas as pd

from RL.env_v2 import PortfolioEnvV2


def make_test_data():
    """Small synthetic dataset with known daily returns."""
    rows = []

    for i in range(5):
        row = {}

        for asset in ["equity", "debt", "hybrid", "liquid"]:
            row[f"{asset}_return"] = 0.0
            row[f"{asset}_vol_30d"] = 0.1

        row["nifty_return"] = 0.0
        row["nifty_vol_30d"] = 0.1
        row["nifty_rsi_14"] = 0.5
        row["nifty_sma_ratio"] = 0.0
        row["nifty_macd_diff"] = 0.0

        rows.append(row)

    return pd.DataFrame(rows)


class TestPortfolioEnvV2(unittest.TestCase):

    def test_observation_shape(self):
        env = PortfolioEnvV2(make_test_data())
        obs, _ = env.reset()

        self.assertEqual(obs.shape, (18,))
        self.assertEqual(obs.dtype, np.float32)

    def test_allocation_sums_to_one(self):
        env = PortfolioEnvV2(make_test_data())
        env.reset()

        env.step(np.array([1, 2, 3, 4], dtype=np.float32))

        self.assertAlmostEqual(
            float(env.weights.sum()),
            1.0,
            places=6,
        )

    def test_no_growth_without_returns_or_costs(self):
        env = PortfolioEnvV2(
            make_test_data(),
            transaction_cost=0.0,
        )
        env.reset()

        for _ in range(4):
            env.step(np.zeros(4, dtype=np.float32))

        self.assertAlmostEqual(
            env.portfolio_value,
            100000.0,
            places=4,
        )

    def test_next_day_returns(self):
        df = make_test_data()

        # Today has no return; tomorrow equity gains 10%.
        df.loc[1, "equity_return"] = 0.10

        env = PortfolioEnvV2(
            df,
            transaction_cost=0.0,
        )

        env.reset()
        env.step(np.zeros(4, dtype=np.float32))

        # 25% equity * 10% growth = 2.5% portfolio growth.
        self.assertAlmostEqual(
            env.portfolio_value,
            102500.0,
            places=4,
        )

    def test_no_rebalance_below_threshold(self):
        env = PortfolioEnvV2(
            make_test_data(),
            rebalance_threshold=0.03,
        )
        env.reset()

        # Equal action gives equal weights: no change required.
        env.step(np.zeros(4, dtype=np.float32))

        self.assertEqual(
            env.history[0]["transaction_fee"],
            0.0,
        )

    def test_invalid_risk_profile(self):
        with self.assertRaises(ValueError):
            PortfolioEnvV2(
                make_test_data(),
                risk_profile=1.5,
            )

    def test_portfolio_accounting_after_rebalance(self):
        df = make_test_data()

        # Equity gains 20% on the next day.
        df.loc[1, "equity_return"] = 0.20

        env = PortfolioEnvV2(
            df,
            transaction_cost=0.001,
            rebalance_threshold=0.0,
        )

        env.reset()

        # First day: maintain an equal-weight allocation.
        env.step(np.zeros(4, dtype=np.float32))

        # Second day: shift most capital away from equity.
        env.step(
            np.array(
                [-5.0, 2.0, 2.0, 2.0],
                dtype=np.float32,
            )
        )

        # Total holdings must match reported portfolio value.
        self.assertAlmostEqual(
            env.portfolio_value,
            float(env.asset_capital.sum()),
            places=5,
        )

        # Cost basis must remain non-negative.
        self.assertTrue(
            np.all(env.cost_basis >= 0)
        )

        # Taxes cannot be negative.
        self.assertGreaterEqual(
            env.history[-1]["tax_paid"],
            0,
        )

        # Transaction fees cannot be negative.
        self.assertGreaterEqual(
            env.history[-1]["transaction_fee"],
            0,
        )

    def test_exact_tax_on_partial_equity_sale(self):
        df = make_test_data()

        # Equity grows by 20% on the first simulated day.
        df.loc[1, "equity_return"] = 0.20

        env = PortfolioEnvV2(
            df,
            transaction_cost=0.0,
            rebalance_threshold=0.0,
            initial_balance=100000.0,
        )

        env.reset()

        # Initial equity holding: Rs 25,000
        env.step(np.zeros(4, dtype=np.float32))

        # After growth:
        # Equity market value = Rs 30,000
        # Equity purchase cost = Rs 25,000
        equity_value = float(env.asset_capital[0])
        equity_cost = float(env.cost_basis[0])

        self.assertAlmostEqual(
            equity_value,
            30000.0,
            places=4,
        )

        self.assertAlmostEqual(
            equity_cost,
            25000.0,
            places=4,
        )

        # Shift portfolio away from equity.
        env.step(
            np.array(
                [-5.0, 2.0, 2.0, 2.0],
                dtype=np.float32,
            )
        )

        # Tax should equal:
        # Realized profit x assumed equity tax rate.
        equity_sold = equity_value - env.asset_capital[0]

        realized_profit = equity_sold * (
            (equity_value - equity_cost) / equity_value
        )

        expected_tax = realized_profit * 0.20

        self.assertAlmostEqual(
            env.history[-1]["tax_paid"],
            expected_tax,
            places=2,
        )

        # Remaining equity cost basis should decrease
        # in proportion to the amount sold.
        expected_remaining_basis = equity_cost * (
            env.asset_capital[0] / equity_value
        )

        self.assertAlmostEqual(
            env.cost_basis[0],
            expected_remaining_basis,
            places=2,
        )


if __name__ == "__main__":
    unittest.main()
