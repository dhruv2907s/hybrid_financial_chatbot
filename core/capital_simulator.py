# core/capital_simulator.py

import numpy as np

class CapitalSimulator:

    def simulate(
        self,
        win_rate,
        reward_risk_ratio,
        initial_capital=100000,
        risk_percent=0.01,
        n_trades=200,
        simulations=500
    ):

        final_capitals = []

        for _ in range(simulations):

            capital = initial_capital

            for _ in range(n_trades):

                risk_amount = capital * risk_percent

                if np.random.rand() < win_rate:
                    capital += risk_amount * reward_risk_ratio
                else:
                    capital -= risk_amount

                if capital <= 0:
                    capital = 0
                    break

            final_capitals.append(capital)

        ruin_probability = sum(c == 0 for c in final_capitals) / simulations

        return {
            "ruin_probability": float(ruin_probability),
            "median_final_capital": float(np.median(final_capitals))
        }