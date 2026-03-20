# core/portfolio.py

import numpy as np
import pandas as pd


class PortfolioRisk:

    def compute_portfolio_volatility(self, price_dict: dict, weights: dict):

        returns_df = pd.DataFrame({
            t: np.log(p / p.shift(1)).dropna()
            for t, p in price_dict.items()
        }).dropna()

        weight_vector = np.array([weights[t] for t in returns_df.columns])
        weight_vector = weight_vector / weight_vector.sum()

        cov_matrix = returns_df.cov().values

        portfolio_variance = weight_vector.T @ cov_matrix @ weight_vector
        portfolio_volatility = np.sqrt(portfolio_variance)

        return float(portfolio_volatility)
