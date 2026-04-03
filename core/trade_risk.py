class TradeRiskEngine:

    def calculate_trade_with_context(
        self,
        ctx,
        entry_price,
        stop_loss,
        take_profit,
        account_size
    ):
        risk_per_share = abs(entry_price - stop_loss)

        if risk_per_share == 0:
            return {"error": "Stop loss cannot equal entry price."}

        reward_per_share = abs(take_profit - entry_price)

        # 🔥 1. Base risk %
        base_risk = ctx.adjusted_risk_percent or 0.01

        # 🔥 2. Reduce risk if asset is risky
        risk_score = ctx.asset_metrics["risk_score"]
        risk_adjustment = max(0.3, 1 - risk_score * 10)

        # 🔥 3. Regime penalty
        if ctx.regime["regime"] == "high_vol":
            regime_factor = 0.7
        elif ctx.regime["regime"] == "low_vol":
            regime_factor = 1.2
        else:
            regime_factor = 1.0

        final_risk_percent = base_risk * risk_adjustment * regime_factor

        capital_at_risk = account_size * final_risk_percent

        position_size = capital_at_risk / risk_per_share
        total_exposure = position_size * entry_price

        rr_ratio = reward_per_share / risk_per_share

        return {
            "risk_per_share": round(risk_per_share, 2),
            "reward_per_share": round(reward_per_share, 2),
            "position_size": int(position_size),
            "total_exposure": round(total_exposure, 2),
            "risk_reward_ratio": round(rr_ratio, 2),
            "capital_risk_percent": round(final_risk_percent * 100, 2),
            "risk_adjustment_factor": risk_adjustment,
            "regime_factor": regime_factor
        }