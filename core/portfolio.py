# core/portfolio.py

import numpy as np
import pandas as pd


class PortfolioRisk:

        def compute_portfolio_volatility(self, price_dict, weights):

            returns_dict = {}

            for t, p in price_dict.items():
                if p is None or len(p) < 2:
                    continue

                returns = np.log(p / p.shift(1)).dropna()

                if len(returns) > 0:
                    returns_dict[t] = returns

            if len(returns_dict) < 2:
                raise ValueError("Not enough valid assets for portfolio")

            returns_df = pd.DataFrame(returns_dict).dropna()

            # 🔥 HANDLE BOTH LIST + DICT
            if isinstance(weights, list):
                if len(weights) != len(returns_df.columns):
                    raise ValueError("Weights length mismatch")
                weight_vector = np.array(weights)

            elif isinstance(weights, dict):
                weight_vector = np.array([weights[t] for t in returns_df.columns])

            else:
                raise ValueError("Weights must be list or dict")

            # Normalize weights
            weight_vector = weight_vector / weight_vector.sum()

            cov_matrix = returns_df.cov().values

            portfolio_variance = weight_vector.T @ cov_matrix @ weight_vector
            portfolio_volatility = np.sqrt(portfolio_variance)

            return float(portfolio_volatility)