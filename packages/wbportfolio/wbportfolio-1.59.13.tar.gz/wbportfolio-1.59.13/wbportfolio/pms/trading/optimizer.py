import math

import cvxpy as cp
import numpy as np

from wbportfolio.pms.typing import TradeBatch


class TradeShareOptimizer:
    def __init__(self, batch: TradeBatch, portfolio_total_value: float):
        self.batch = batch
        self.portfolio_total_value = portfolio_total_value

    def optimize(self, target_cash: float = 0.99):
        try:
            return self.optimize_trade_share(target_cash)
        except ValueError:
            return self.floor_trade_share()

    def optimize_trade_share(self, target_cash: float = 0.01):
        prices_fx_portfolio = np.array([trade.price_fx_portfolio for trade in self.batch.trades])
        target_allocs = np.array([trade.target_weight for trade in self.batch.trades])

        # Decision variable: number of shares (integers)
        shares = cp.Variable(len(prices_fx_portfolio), integer=True)

        # Calculate portfolio values
        portfolio_values = cp.multiply(shares, prices_fx_portfolio)

        # Target values based on allocations
        target_values = self.portfolio_total_value * target_allocs

        # Objective: minimize absolute deviation from target values
        objective = cp.Minimize(cp.sum(cp.abs(portfolio_values - target_values)))

        # Constraints
        constraints = [
            shares >= 0,  # No short selling
            cp.sum(portfolio_values) <= self.portfolio_total_value,  # Don't exceed budget
            cp.sum(portfolio_values) >= (1.0 - target_cash) * self.portfolio_total_value,  # Use at least 99% of budget
        ]

        # Solve
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.CBC)

        if problem != "optimal":
            raise ValueError(f"Optimization failed: {problem.status}")

        shares_result = shares.value.astype(int)
        return TradeBatch(
            [
                trade.normalize_target(target_shares=shares_result[index])
                for index, trade in enumerate(self.batch.trades)
            ]
        )

    def floor_trade_share(self):
        return TradeBatch(
            [trade.normalize_target(target_shares=math.floor(trade.target_shares)) for trade in self.batch.trades]
        )
