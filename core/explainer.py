# core/explainer.py

class RiskExplainer:

    def explain_asset(self, ticker, metrics):

        return (
            f"{ticker} Statistical Risk:\n"
            f"- Volatility: {metrics['volatility']:.5f}\n"
            f"- Expected Shortfall: {metrics['expected_shortfall']:.5f}\n"
            f"- Risk Score: {metrics['risk_score']:.5f}"
        )

    def explain_trade(self, metrics):

        return (
            "Trade Risk Analysis:\n"
            f"- Risk per share: ${metrics['risk_per_share']}\n"
            f"- Reward per share: ${metrics['reward_per_share']}\n"
            f"- Risk/Reward Ratio: {metrics['risk_reward_ratio']}\n"
            f"- Suggested position size: {metrics['position_size']} shares\n"
            f"- Total Dollar Risk: ${metrics['total_risk_dollars']}"
        )
    def explain_full(self, ctx):

        forecast_part = (
            f"\n- Forecast Risk: {ctx.forecast_risk['forecast_integrated_risk']:.5f}"
            if ctx.forecast_risk else ""
        )

        return (
            f"Full Risk Analysis for {ctx.ticker}:\n\n"
            f"- Volatility: {ctx.asset_metrics['volatility']:.5f}\n"
            f"- Expected Shortfall: {ctx.asset_metrics['expected_shortfall']:.5f}\n"
            f"- Risk Score: {ctx.asset_metrics['risk_score']:.5f}\n\n"
            f"- Market Regime: {ctx.regime['regime']}\n"
            f"- Adjusted Risk %: {ctx.adjusted_risk_percent*100:.2f}%\n"
            f"- Stress Drawdown: {ctx.stress['stress_drawdown']:.2%}"
            f"{forecast_part}\n\n"
            f"Recommendation: {ctx.recommendation}"
        )