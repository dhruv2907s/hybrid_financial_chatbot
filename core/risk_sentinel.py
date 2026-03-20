# core/risk_sentinel.py

import numpy as np
import pandas as pd


class RiskSentinel:

    def __init__(self, confidence_level=0.95):
        self.confidence_level = confidence_level

    def compute_log_returns(self, prices: pd.Series):
        return np.log(prices / prices.shift(1)).dropna()

    def compute_volatility(self, returns: pd.Series):
        return returns.std()

    def compute_var(self, returns: pd.Series):
        return np.percentile(
            returns,
            (1 - self.confidence_level) * 100
        )

    def compute_expected_shortfall(self, returns: pd.Series):
        var = self.compute_var(returns)
        tail = returns[returns <= var]
        return tail.mean() if len(tail) > 0 else 0.0

    def assess_asset(self, price_series: pd.Series):
        returns = self.compute_log_returns(price_series)

        vol = self.compute_volatility(returns)
        es = self.compute_expected_shortfall(returns)

        risk_score = 0.6 * vol + 0.4 * abs(es)

        return {
            "volatility": float(vol),
            "expected_shortfall": float(es),
            "risk_score": float(risk_score)
        }
