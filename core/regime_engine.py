# core/regime_engine.py

import numpy as np
import pandas as pd


class RegimeEngine:

    def __init__(self, window=20):
        """
        window: rolling window size for volatility
        """
        self.window = window

    def detect_regime(self, returns: pd.Series):

       
        returns = returns.squeeze().dropna()

        rolling_vol = returns.rolling(self.window).std().dropna()

        if rolling_vol.empty:
            return {
                "regime": "unknown",
                "current_vol": None,
                "low_threshold": None,
                "high_threshold": None
            }

        current_vol = float(rolling_vol.iloc[-1])

        # Distribution-based thresholds
        low_threshold = float(rolling_vol.quantile(0.25))
        high_threshold = float(rolling_vol.quantile(0.75))

        if current_vol < low_threshold:
            regime = "low_vol"
        elif current_vol > high_threshold:
            regime = "high_vol"
        else:
            regime = "normal_vol"

        return {
            "regime": regime,
            "current_vol": current_vol,
            "low_threshold": low_threshold,
            "high_threshold": high_threshold
        }

    def adaptive_risk_percent(self, regime, base_risk=0.01):
        """
        Dynamic capital allocation rule based on regime.
        """

        if regime == "high_vol":
            return base_risk * 0.5
        elif regime == "low_vol":
            return base_risk * 1.2
        else:
            return base_risk