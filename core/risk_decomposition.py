# core/risk_decomposition.py

import numpy as np
import pandas as pd

class RiskDecomposition:

    def compute_marginal_risk_contribution(self, price_dict, weights):

        returns_df = pd.DataFrame({
            t: np.log(p / p.shift(1)).dropna()
            for t, p in price_dict.items()
        }).dropna()

        weights_vector = np.array([weights[t] for t in returns_df.columns])
        weights_vector = weights_vector / weights_vector.sum()

        cov_matrix = returns_df.cov().values

        portfolio_vol = np.sqrt(
            weights_vector.T @ cov_matrix @ weights_vector
        )

        marginal_contrib = (
            weights_vector *
            (cov_matrix @ weights_vector)
        ) / portfolio_vol

        risk_percentages = marginal_contrib / marginal_contrib.sum()

        return {
            ticker: {
                "marginal_contribution": float(marginal_contrib[i]),
                "risk_percentage": float(risk_percentages[i])
            }
            for i, ticker in enumerate(returns_df.columns)
        }