import numpy as np

class StressTestEngine:

    def apply_sigma_shock(self, returns, sigma=2):
        """
        Apply controlled volatility shock (NOT extreme).
        """

        # Safety: remove NaNs
        returns = returns[~np.isnan(returns)]

        if len(returns) == 0:
            return returns

        std = np.std(returns)

        # Apply moderate shock
        shocked_returns = returns - sigma * std

        # 🔥 CLAMP to realistic bounds (CRITICAL)
        shocked_returns = np.clip(shocked_returns, -0.2, 0.2)

        return shocked_returns


    def compute_drawdown(self, returns):
        """
        Compute realistic max drawdown.
        """

        if len(returns) == 0:
            return 0.0

        cumulative = (1 + returns).cumprod()

        peak = np.maximum.accumulate(cumulative)

        drawdown = (cumulative - peak) / peak

        dd = float(drawdown.min())

        # 🔥 CAP extreme unrealistic crashes
        dd = max(dd, -0.5)

        return dd