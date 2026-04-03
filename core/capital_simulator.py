import numpy as np

class CapitalSimulator:

    def _to_numpy(self, returns):
        if hasattr(returns, "dropna"):
            returns = returns.dropna().values
        return np.array(returns).reshape(-1)

    def simulate_with_context(
        self,
        ctx,
        returns,
        initial_capital=100000,
        n_trades=50,
        n_sim=500
    ):

        returns = self._to_numpy(returns)

        if len(returns) < 10:
            return {"error": "Insufficient return data"}

        # -------- CLEAN RETURNS --------
        returns = np.clip(returns, -0.2, 0.2)

        # -------- REGIME --------
        regime = ctx.regime["regime"] if ctx else "normal_vol"

        base_risk = 0.03

        if regime == "high_vol":
            risk_pct = base_risk * 0.5
        elif regime == "low_vol":
            risk_pct = base_risk * 1.2
        else:
            risk_pct = base_risk

        # -------- RISK SCORE ADJUSTMENT --------
        risk_score = ctx.asset_metrics["risk_score"] if ctx else 0.5
        risk_adjustment = max(0.5, 1 - risk_score * 5)
        risk_pct *= risk_adjustment

        # -------- TRADE RR --------
        rr = 1.0
        if ctx and ctx.trade:
            rr = max(0.5, min(3.0, ctx.trade.get("risk_reward_ratio", 1)))

        final_capitals = []
        drawdowns = []

        for _ in range(n_sim):

            capital = initial_capital
            peak = capital
            max_dd = 0

            for _ in range(n_trades):

                if capital <= initial_capital * 0.2:
                    break

                sampled_return = np.random.choice(returns)

                # -------- TRADE LOGIC --------
                if sampled_return > 0:
                    pnl = risk_pct * rr
                else:
                    pnl = -risk_pct

                capital *= (1 + pnl)

                peak = max(peak, capital)
                dd = (peak - capital) / peak
                max_dd = max(max_dd, dd)

            final_capitals.append(capital)
            drawdowns.append(max_dd)

        final_capitals = np.array(final_capitals)

        return {
            "median_final_capital": float(np.median(final_capitals)),
            "mean_final_capital": float(np.mean(final_capitals)),
            "avg_drawdown": float(np.mean(drawdowns)),
            "risk_per_trade": float(risk_pct)
        }