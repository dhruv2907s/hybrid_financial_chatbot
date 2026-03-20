# core/recommender.py

class RecommendationEngine:

    def recommend_asset(self, asset_risk: dict):

        score = asset_risk["risk_score"]

        if score < 0.01:
            return "Low statistical risk. Suitable for core allocation."
        elif score < 0.03:
            return "Moderate risk. Allocate proportionally."
        else:
            return "High statistical risk. Limit exposure."

    def recommend_trade(self, trade_metrics: dict):

        rr = trade_metrics["risk_reward_ratio"]

        if rr >= 3:
            return "Favorable trade setup (>= 1:3 RR)."
        elif rr >= 2:
            return "Acceptable trade setup."
        else:
            return "Unfavorable risk-reward. Reconsider trade."
