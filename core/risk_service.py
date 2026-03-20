# core/risk_service.py

from core.risk_sentinel import RiskSentinel
from core.portfolio import PortfolioRisk
from core.trade_risk import TradeRiskEngine
from core.recommender import RecommendationEngine
from core.explainer import RiskExplainer
from core.forecast_risk import ForecastRiskEngine
from core.regime_engine import RegimeEngine
from core.risk_decomposition import RiskDecomposition
from core.stress_test import StressTestEngine
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
        self.stress_engine = StressTestEngine()
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

        vol = self.portfolio_engine.compute_portfolio_volatility(price_dict, weights)

        decomposition = self.decomposition_engine.compute_marginal_risk_contribution(
            price_dict, weights
        )

        stress = {
            t: self.evaluate_stress_test(p)
            for t, p in price_dict.items()
        }

        # Explanation (important for demo)
        explanation = f"Portfolio Volatility: {vol:.5f}\n\n"

        explanation += "Risk Contribution:\n"
        for asset, val in decomposition.items():
            explanation += f"- {asset}: {val['risk_percentage']*100:.2f}%\n"

        explanation += "\nStress Test:\n"
        for asset, val in stress.items():
            explanation += f"- {asset}: {val['stress_drawdown']:.2%}\n"

        return {
            "portfolio_volatility": vol,
            "risk_contribution": decomposition,
            "stress": stress,
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

    # -------- Stress Test --------
    def evaluate_stress_test(self, price_series):

        returns = self.asset_engine.compute_log_returns(price_series).dropna()

        if len(returns) < 10:
            return {"stress_drawdown": 0.0}

        shocked_returns = self.stress_engine.apply_sigma_shock(returns)

        drawdown = self.stress_engine.compute_drawdown(shocked_returns)

        # FINAL SAFETY CAP
        drawdown = max(drawdown, -0.5)

        return {
            "stress_drawdown": drawdown
        }

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
        results = self.capital_simulator.simulate(
            win_rate=win_rate,
            reward_risk_ratio=reward_risk_ratio,
            initial_capital=initial_capital
        )

        # Step 7: Attach context (VERY IMPORTANT FOR PAPER)
        results["derived_win_rate"] = win_rate
        results["regime"] = regime
        results["volatility"] = float(vol)

        return results

    # -------- FULL PIPELINE (CORE CONTRIBUTION) --------
    def full_analysis(self, ticker, price_series, predicted_prices=None):

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

        # ---------------- 5. Stress Testing ----------------
        ctx.stress = self.evaluate_stress_test(price_series)

        # ---------------- 6. Capital Simulation ----------------
        ctx.capital = self.evaluate_capital_survival(price_series)

        # ---------------- 7. Composite Risk Score ----------------
        forecast_component = (
            ctx.forecast_risk["forecast_integrated_risk"]
            if ctx.forecast_risk else ctx.asset_metrics["volatility"]
        )

        ctx.summary_score = (
            0.4 * ctx.asset_metrics["risk_score"] +
            0.3 * min(abs(ctx.stress["stress_drawdown"]), 0.5) +
            0.2 * forecast_component +
            0.1 * (1 - ctx.capital["ruin_probability"])
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
        ctx.explanation = f"""
    Full Risk Analysis for {ticker}:

    📊 Statistical Risk:
    - Volatility: {ctx.asset_metrics['volatility']:.4f}
    - Expected Shortfall: {ctx.asset_metrics['expected_shortfall']:.4f}
    - Risk Score: {ctx.asset_metrics['risk_score']:.4f}

    📉 Market Regime:
    - Regime: {ctx.regime['regime']}
    - Adjusted Risk: {ctx.adjusted_risk_percent*100:.2f}%

    ⚠ Stress Scenario:
    - Estimated Drawdown: {ctx.stress['stress_drawdown']:.2%}

    💰 Capital Outlook:
    - Ruin Probability: {ctx.capital['ruin_probability']:.2%}
    - Median Capital: {ctx.capital['median_final_capital']:.2f}

    📈 Composite Risk:
    - Score: {ctx.summary_score:.4f}
    - Level: {ctx.summary_label}

    🧠 Recommendation:
    {ctx.recommendation}
    """

        return ctx