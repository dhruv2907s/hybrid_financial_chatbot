# core/forecast_risk.py

import numpy as np

class ForecastRiskEngine:

    def __init__(self, alpha=0.5, beta=0.3, gamma=0.2):
        """
        alpha -> historical volatility weight
        beta  -> forecast volatility weight
        gamma -> expected shortfall weight
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    def compute_forecast_volatility(self, predicted_prices):
        """
        predicted_prices: array-like future price predictions from TFT
        """
        returns = np.diff(np.log(predicted_prices))
        return np.std(returns)

    def compute_forecast_integrated_risk(
        self,
        historical_vol,
        expected_shortfall,
        predicted_prices
    ):
        forecast_vol = self.compute_forecast_volatility(predicted_prices)

        enhanced_risk = (
            self.alpha * historical_vol +
            self.beta * forecast_vol +
            self.gamma * abs(expected_shortfall)
        )

        if predicted_prices is None or len(predicted_prices) < 2:
            return {
                "historical_vol": historical_vol,
                "forecast_vol": 0.0,
                "forecast_integrated_risk": historical_vol
            }