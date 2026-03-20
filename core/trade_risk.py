import numpy as np

class TradeRiskEngine:

    def calculate_trade(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        account_size: float,
        risk_percent: float = 0.01
    ):
        risk_per_share = abs(entry_price - stop_loss)

        if risk_per_share == 0:
            return {"error": "Stop loss cannot equal entry price."}

        reward_per_share = abs(take_profit - entry_price)

        capital_at_risk = account_size * risk_percent

        position_size = capital_at_risk / risk_per_share

        total_exposure = position_size * entry_price

        rr_ratio = reward_per_share / risk_per_share

        return {
            "risk_per_share": round(risk_per_share, 2),
            "reward_per_share": round(reward_per_share, 2),
            "total_risk_dollars": round(capital_at_risk, 2),
            "position_size": int(position_size),
            "risk_reward_ratio": round(rr_ratio, 2),
            "total_exposure": round(total_exposure, 2),
            "capital_risk_percent": round(risk_percent * 100, 2)
        }

    def suggest_atr_stop(self, entry_price, atr, multiplier=2):
        stop = entry_price - (multiplier * atr)
        return round(stop, 2)
