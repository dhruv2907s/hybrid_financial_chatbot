# core/risk_service.py

from core.risk_sentinel import RiskSentinel
from core.portfolio import PortfolioRisk
from core.trade_risk import TradeRiskEngine
from core.recommender import RecommendationEngine
from core.explainer import RiskExplainer
from core.forecast_risk import ForecastRiskEngine
from core.regime_engine import RegimeEngine
from core.risk_decomposition import RiskDecomposition
from core.capital_simulator import CapitalSimulator
from core.context import RiskContext


class RiskService:

    def __init__(self):
        self.asset_engine = RiskSentinel()
        self.portfolio_engine = PortfolioRisk()
        self.trade_engine = TradeRiskEngine()
        self.recommender = RecommendationEngine()
        self.explainer = RiskExplainer()
        self.forecast_engine = ForecastRiskEngine()
        self.regime_engine = RegimeEngine()
        self.decomposition_engine = RiskDecomposition()
        
        self.capital_simulator = CapitalSimulator()

    # -------- Asset Risk --------
    def evaluate_asset(self, ticker, price_series):

        metrics = self.asset_engine.assess_asset(price_series)

        recommendation = self.recommender.recommend_asset(metrics)
        explanation = self.explainer.explain_asset(ticker, metrics)

        return {
            "metrics": metrics,
            "recommendation": recommendation,
            "explanation": explanation
        }

    # -------- Portfolio Risk (FULL) --------
    def evaluate_portfolio_full(self, price_dict, weights):

        # -------- 1. Statistical Risk --------
        vol = self.portfolio_engine.compute_portfolio_volatility(price_dict, weights)

        decomposition = self.decomposition_engine.compute_marginal_risk_contribution(
            price_dict, weights
        )

        # -------- 2. Asset Risk Integration --------
        asset_risks = {}
        regimes = {}

        for t, p in price_dict.items():
            metrics = self.asset_engine.assess_asset(p)
            asset_risks[t] = metrics["risk_score"]

            returns = self.asset_engine.compute_log_returns(p).dropna()
            regimes[t] = self.regime_engine.detect_regime(returns)["regime"]

        # -------- 3. Explanation --------
        explanation = f"""
    Portfolio Risk Analysis:

    - Portfolio Volatility: {vol:.4f}

    Risk Contribution:
    """

        max_asset = None
        max_risk = 0

        for asset, val in decomposition.items():
            risk_pct = val["risk_percentage"]
            risk_score = asset_risks.get(asset, 0)

            explanation += f"- {asset}: {risk_pct*100:.2f}% (Risk Score: {risk_score:.2f})\n"

            if risk_pct > max_risk:
                max_risk = risk_pct
                max_asset = asset

        # -------- 4. Interpretation --------
        explanation += "\nInterpretation:\n"

        if vol > 0.03:
            explanation += "- Portfolio has HIGH volatility (risky)\n"
        elif vol > 0.015:
            explanation += "- Portfolio has MODERATE risk\n"
        else:
            explanation += "- Portfolio is relatively STABLE\n"

        # -------- 5. Decision Layer --------
        explanation += "\nRecommendations:\n"

        if max_asset:
            explanation += f"- {max_asset} contributes most to risk ({max_risk*100:.2f}%)\n"

            if asset_risks[max_asset] > 0.6:
                explanation += f"- {max_asset} has high intrinsic risk → strong candidate to reduce\n"

            if max_risk > 0.5:
                reduction_ratio = (max_risk - 0.4) / max_risk
                explanation += f"- Reduce {max_asset} exposure by ~{max(0, reduction_ratio)*100:.1f}%\n"

        # Regime-aware advice
        high_vol_assets = [a for a, r in regimes.items() if r == "high_vol"]
        if high_vol_assets:
            explanation += f"- High volatility regime detected in: {', '.join(high_vol_assets)} → reduce aggressive positions\n"

        # Diversification advice
        if len(decomposition) >= 2:
            explanation += "- Diversification can reduce portfolio risk\n"

        return {
            "portfolio_volatility": vol,
            "risk_contribution": decomposition,
            "asset_risk_scores": asset_risks,
            "regimes": regimes,
            "explanation": explanation
        }
    
    # -------- Trade Risk (BASIC) --------
    def evaluate_trade(self, **kwargs):

        metrics = self.trade_engine.calculate_trade(**kwargs)
        recommendation = self.recommender.recommend_trade(metrics)
        explanation = self.explainer.explain_trade(metrics)

        return {
            "metrics": metrics,
            "recommendation": recommendation,
            "explanation": explanation
        }

    # -------- Trade Risk (REGIME-AWARE) --------
    def evaluate_trade_with_context(self, price_series, **kwargs):

        regime = self.evaluate_regime(price_series)

        adjusted_risk = self.regime_engine.adaptive_risk_percent(
            regime["regime"]
        )

        kwargs["risk_percent"] = adjusted_risk

        metrics = self.trade_engine.calculate_trade(**kwargs)

        explanation = (
            self.explainer.explain_trade(metrics)
            + f"\n\nMarket Regime: {regime['regime']}"
            + f"\nAdjusted Risk %: {adjusted_risk*100:.2f}%"
        )

        return {
            "metrics": metrics,
            "regime": regime,
            "adjusted_risk_percent": adjusted_risk,
            "explanation": explanation
        }

    # -------- Forecast Risk --------
    def evaluate_forecast_asset(self, ticker, price_series, predicted_prices):

        base_metrics = self.asset_engine.assess_asset(price_series)

        forecast_metrics = self.forecast_engine.compute_forecast_integrated_risk(
            historical_vol=base_metrics["volatility"],
            expected_shortfall=base_metrics["expected_shortfall"],
            predicted_prices=predicted_prices
        )

        return {
            "base_metrics": base_metrics,
            "forecast_metrics": forecast_metrics
        }

    # -------- Regime --------
    def evaluate_regime(self, price_series):

        returns = self.asset_engine.compute_log_returns(price_series)
        return self.regime_engine.detect_regime(returns)

    # -------- Risk Contribution --------
    def evaluate_risk_contribution(self, price_dict, weights):

        return self.decomposition_engine.compute_marginal_risk_contribution(
            price_dict,
            weights
        )



    # -------- Capital Survival --------
    def evaluate_capital_survival(
        self,
        price_series,
        initial_capital=100000
    ):

        # Step 1: Compute returns
        returns = self.asset_engine.compute_log_returns(price_series).dropna()

        if len(returns) < 20:
            return {
                "ruin_probability": 0.0,
                "median_final_capital": initial_capital
            }

        # Step 2: Get volatility (risk signal)
        vol = returns.std()

        # Step 3: Get regime
        regime_info = self.regime_engine.detect_regime(returns)
        regime = regime_info["regime"]

        # Step 4: Map volatility → win probability
        win_rate = max(0.3, min(0.7, 0.6 - vol))

        # Step 5: Adjust reward-risk based on regime
        if regime == "high_vol":
            reward_risk_ratio = 1.5
        elif regime == "low_vol":
            reward_risk_ratio = 2.5
        else:
            reward_risk_ratio = 2.0

        # Step 6: Simulate capital
        results = self.capital_simulator.simulate_with_context(
            ctx=None,  # or create dummy context if needed
            initial_capital=initial_capital,
            returns=returns,
            n_sim=300,
            n_trades=100
        )

        # Step 7: Attach context (VERY IMPORTANT FOR PAPER)
        results["derived_win_rate"] = win_rate
        results["regime"] = regime
        results["volatility"] = float(vol)

        return results

    # -------- FULL PIPELINE (CORE CONTRIBUTION) --------
    def full_analysis(self, ticker, price_series, predicted_prices=None,trade_input=None,capital_input=None):

        ctx = RiskContext(ticker)
        ctx.price_series = price_series
        ctx.predicted_prices = predicted_prices

        # ---------------- 1. Asset Risk ----------------
        ctx.asset_metrics = self.asset_engine.assess_asset(price_series)

        # ---------------- 2. Regime Detection ----------------
        returns = self.asset_engine.compute_log_returns(price_series).dropna()
        ctx.regime = self.regime_engine.detect_regime(returns)

        # ---------------- 3. Adaptive Risk ----------------
        ctx.adjusted_risk_percent = self.regime_engine.adaptive_risk_percent(
            ctx.regime["regime"]
        )

        # 🔥 Regime-adjusted risk score
        ctx.asset_metrics["regime_adjusted_risk_score"] = (
            ctx.asset_metrics["risk_score"] * (1 + ctx.adjusted_risk_percent)
        )

        # ---------------- 4. Forecast Risk ----------------
        ctx.forecast_risk = None

        if predicted_prices is not None:
            ctx.forecast_risk = self.forecast_engine.compute_forecast_integrated_risk(
                historical_vol=ctx.asset_metrics["volatility"],
                expected_shortfall=ctx.asset_metrics["expected_shortfall"],
                predicted_prices=predicted_prices
            )
        if trade_input:
            ctx.trade = self.trade_engine.calculate_trade_with_context(
                ctx,
                entry_price=trade_input["entry_price"],
                stop_loss=trade_input["stop_loss"],
                take_profit=trade_input["take_profit"],
                account_size=trade_input["account_size"]
            )
        
        # ---------------- 6. Capital Simulation ----------------
        if capital_input:
            returns = self.asset_engine.compute_log_returns(price_series).dropna()

            ctx.capital = self.capital_simulator.simulate_with_context(
                ctx=ctx,
                returns=returns,
                initial_capital=capital_input.get("initial_capital", 100000),
                n_trades=capital_input.get("n_trades", 50),
                n_sim=capital_input.get("simulations", 500)
            )
        # ---------------- 7. Composite Risk Score ----------------
        forecast_component = (
            ctx.forecast_risk["forecast_integrated_risk"]
            if ctx.forecast_risk else ctx.asset_metrics["volatility"]
        )
        dd = ctx.capital.get("avg_drawdown", 0) if ctx.capital else 0.5
        capital_component = max(0, 1 - dd)
        ctx.summary_score = (
            0.4 * ctx.asset_metrics["risk_score"] +
            0.2 * forecast_component +
            0.1 * capital_component
        )

        # ---------------- 8. Risk Label ----------------
        if ctx.summary_score < 0.02:
            ctx.summary_label = "Low Risk"
        elif ctx.summary_score < 0.05:
            ctx.summary_label = "Moderate Risk"
        else:
            ctx.summary_label = "High Risk"

        # ---------------- 9. Recommendation ----------------
        ctx.recommendation = self.recommender.recommend_asset(ctx.asset_metrics)
    
        # ---------------- 10. Explanation ----------------
        # ---- Safe Capital Block ----
        capital_text = ""

        if ctx.capital:
            dd = ctx.capital.get("avg_drawdown", 0)

            capital_text = f"""
                Capital Outlook:
                - Median Capital: {ctx.capital['median_final_capital']:.2f}
                - Avg Drawdown: {dd:.2%}
                """

        # ---- TRADE MODE (ONLY TRADE) ----
        trade_quality = ""
        if ctx.trade:

            if "error" in ctx.trade:
                ctx.explanation = f"""
         Trade Evaluation for {ticker}:

         Error: {ctx.trade['error']}

        Please check:
        - Entry ≠ Stop Loss
        - Proper trade inputs
        """
            else:
                # 🔥 ADD THIS (NEW LOGIC)
                rr = ctx.trade.get("risk_reward_ratio", 0)

                if rr < 2:
                    trade_quality = "❌ Trade Quality: Poor (RR < 2)"
                elif rr < 3:
                    trade_quality = "⚠ Trade Quality: Acceptable"
                else:
                    trade_quality = "✅ Trade Quality: Strong"

                # 🔥 UPDATED EXPLANATION
                ctx.explanation = f"""
        Trade Evaluation for {ticker}:

        - Position Size: {ctx.trade.get('position_size', 'N/A')} shares
        - Risk/Reward Ratio: {ctx.trade.get('risk_reward_ratio', 'N/A')}
        - Capital at Risk: {ctx.trade.get('capital_risk_percent', 'N/A')}%
        - Exposure: {ctx.trade.get('total_exposure', 0):.2f}

        Market Context:
        - Regime: {ctx.regime['regime']}
        - Volatility: {ctx.asset_metrics['volatility']:.4f}
        

         Recommendation:
        {ctx.recommendation}

        {trade_quality}
        """
        else:
            # ---- NORMAL FULL ANALYSIS ----
            ctx.explanation = f"""
        Full Risk Analysis for {ticker}:

        Statistical Risk:
        - Volatility: {ctx.asset_metrics['volatility']:.4f}
        - Expected Shortfall: {ctx.asset_metrics['expected_shortfall']:.4f}
        - Risk Score: {ctx.asset_metrics['risk_score']:.4f}

        Market Regime:
        - Regime: {ctx.regime['regime']}
        - Adjusted Risk: {ctx.adjusted_risk_percent*100:.2f}%

        {capital_text}

        Composite Risk:
        - Score: {ctx.summary_score:.4f}
        - Level: {ctx.summary_label}

        Recommendation:
        {ctx.recommendation}
        """
        return ctx