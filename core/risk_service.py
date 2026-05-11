# core/risk_service.py

import numpy as np
import pandas as pd
import yfinance as yf

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

    # ────────────────────────────────────────────
    # Portfolio Basket Analysis
    # ────────────────────────────────────────────
    def analyze_portfolio_basket(self, holdings: dict):
        """
        holdings: {"AAPL": 5000, "TSLA": 3000, "GLD": 2000}
        """
        tickers = list(holdings.keys())

        data = yf.download(tickers, period="1y", progress=False)['Close']
        if isinstance(data, pd.Series):
            data = data.to_frame(name=tickers[0])

        returns = data.pct_change().dropna()

        total_value = sum(holdings.values())
        weights = np.array([holdings[t] / total_value for t in tickers])

        cov_matrix = returns.cov() * 252
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)

        individual_vols = [returns[t].std() * np.sqrt(252) for t in tickers]
        weighted_avg_vol = sum(v * w for v, w in zip(individual_vols, weights))
        benefit = (weighted_avg_vol - portfolio_volatility) / (weighted_avg_vol + 1e-8)

        return {
            "total_value": total_value,
            "annual_volatility": float(portfolio_volatility),
            "diversification_benefit": float(benefit),
            "tickers": tickers,
        }

    # ────────────────────────────────────────────
    # Asset Risk
    # ────────────────────────────────────────────
    def evaluate_asset(self, ticker, price_series):
        metrics = self.asset_engine.assess_asset(price_series)
        recommendation = self.recommender.recommend_asset(metrics)
        explanation = self.explainer.explain_asset(ticker, metrics)
        return {"metrics": metrics, "recommendation": recommendation, "explanation": explanation}

    # ────────────────────────────────────────────
    # Trade Risk (basic)
    # ────────────────────────────────────────────
    def evaluate_trade(self, **kwargs):
        metrics = self.trade_engine.calculate_trade(**kwargs)
        recommendation = self.recommender.recommend_trade(metrics)
        explanation = self.explainer.explain_trade(metrics)
        return {"metrics": metrics, "recommendation": recommendation, "explanation": explanation}

    # ────────────────────────────────────────────
    # Trade Risk (regime-aware)
    # ────────────────────────────────────────────
    def evaluate_trade_with_context(self, price_series, **kwargs):
        regime = self.evaluate_regime(price_series)
        adjusted_risk = self.regime_engine.adaptive_risk_percent(regime["regime"])
        kwargs["risk_percent"] = adjusted_risk
        metrics = self.trade_engine.calculate_trade(**kwargs)
        explanation = (
            self.explainer.explain_trade(metrics)
            + f"\n\nMarket Regime: {regime['regime']}"
            + f"\nAdjusted Risk %: {adjusted_risk * 100:.2f}%"
        )
        return {
            "metrics": metrics,
            "regime": regime,
            "adjusted_risk_percent": adjusted_risk,
            "explanation": explanation,
        }

    # ────────────────────────────────────────────
    # Regime
    # ────────────────────────────────────────────
    def evaluate_regime(self, price_series):
        returns = self.asset_engine.compute_log_returns(price_series)
        return self.regime_engine.detect_regime(returns)

    # ────────────────────────────────────────────
    # Risk Contribution
    # ────────────────────────────────────────────
    def evaluate_risk_contribution(self, price_dict, weights):
        return self.decomposition_engine.compute_marginal_risk_contribution(price_dict, weights)

    # ────────────────────────────────────────────
    # Capital Survival
    # ────────────────────────────────────────────
    def evaluate_capital_survival(self, price_series, initial_capital=100000):
        returns = self.asset_engine.compute_log_returns(price_series).dropna()
        if len(returns) < 20:
            return {"ruin_probability": 0.0, "median_final_capital": initial_capital}
        vol = returns.std()
        regime_info = self.regime_engine.detect_regime(returns)
        regime = regime_info["regime"]
        win_rate = max(0.3, min(0.7, 0.6 - vol))
        reward_risk_ratio = {"high_vol": 1.5, "low_vol": 2.5}.get(regime, 2.0)
        results = self.capital_simulator.simulate_with_context(
            ctx=None,
            initial_capital=initial_capital,
            returns=returns,
            n_sim=300,
            n_trades=100,
        )
        results["derived_win_rate"] = win_rate
        results["regime"] = regime
        results["volatility"] = float(vol)
        return results

    # ────────────────────────────────────────────
    # FULL PIPELINE
    # ────────────────────────────────────────────
    def full_analysis(
        self,
        ticker,
        price_series,
        predicted_prices=None,
        trade_input=None,
        capital_input=None,
    ):
        ctx = RiskContext(ticker)
        ctx.price_series = price_series
        ctx.predicted_prices = predicted_prices

        # 1. Asset Risk
        ctx.asset_metrics = self.asset_engine.assess_asset(price_series)

        # 2. Regime Detection
        returns = self.asset_engine.compute_log_returns(price_series).dropna()
        ctx.regime = self.regime_engine.detect_regime(returns)

        # 3. Adaptive Risk
        ctx.adjusted_risk_percent = self.regime_engine.adaptive_risk_percent(
            ctx.regime["regime"]
        )
        ctx.asset_metrics["regime_adjusted_risk_score"] = ctx.asset_metrics[
            "risk_score"
        ] * (1 + ctx.adjusted_risk_percent)

        # 4. Forecast Risk
        ctx.forecast_risk = None
        if predicted_prices is not None:
            ctx.forecast_risk = self.forecast_engine.compute_forecast_integrated_risk(
                historical_vol=ctx.asset_metrics["volatility"],
                expected_shortfall=ctx.asset_metrics["expected_shortfall"],
                predicted_prices=predicted_prices,
            )

        # 5. Trade Analysis
       # 5. Trade Analysis
        ctx.trade = None
        if trade_input:
            ctx.trade = self.trade_engine.calculate_trade_with_context(
                ctx,
                entry_price=trade_input["entry_price"],
                stop_loss=trade_input["stop_loss"],
                take_profit=trade_input["take_profit"],
                account_size=trade_input["account_size"],
            )
            # 🔥 INJECT THE INPUTS BACK INTO THE REPORT SO IT DOESN'T SAY 0.00
            if ctx.trade and "error" not in ctx.trade:
                ctx.trade["entry_price"] = trade_input["entry_price"]
                ctx.trade["stop_loss"] = trade_input["stop_loss"]
                ctx.trade["take_profit"] = trade_input["take_profit"]
                ctx.trade["account_size"] = trade_input["account_size"]

        # 6. Capital Simulation
        ctx.capital = None
        if capital_input:
            sim_returns = self.asset_engine.compute_log_returns(price_series).dropna()
            ctx.capital = self.capital_simulator.simulate_with_context(
                ctx=ctx,
                returns=sim_returns,
                initial_capital=capital_input.get("initial_capital", 100000),
                n_trades=capital_input.get("n_trades", 50),
                n_sim=capital_input.get("simulations", 300),
            )

        # 7. Composite Risk Score
        forecast_component = (
            ctx.forecast_risk["forecast_integrated_risk"]
            if ctx.forecast_risk
            else ctx.asset_metrics["volatility"]
        )
        dd = ctx.capital.get("avg_drawdown", 0.5) if ctx.capital else 0.5
        capital_component = max(0, 1 - dd)
        ctx.summary_score = (
            0.4 * ctx.asset_metrics["risk_score"]
            + 0.2 * forecast_component
            + 0.1 * capital_component
        )

        # 8. Risk Label
        if ctx.summary_score < 0.02:
            ctx.summary_label = "LOW RISK"
        elif ctx.summary_score < 0.05:
            ctx.summary_label = "MODERATE RISK"
        else:
            ctx.summary_label = "HIGH RISK"

        # 9. Recommendation
        ctx.recommendation = self.recommender.recommend_asset(ctx.asset_metrics)

        # 10. Build Report
        ctx.explanation = self._build_report(ctx, ticker)
        return ctx

    # ────────────────────────────────────────────
    # Report Builder
    # ────────────────────────────────────────────
    def _build_report(self, ctx, ticker: str) -> str:
        ticker = ticker.upper()
        vol = ctx.asset_metrics.get("volatility", 0)
        risk_score = ctx.asset_metrics.get("risk_score", 0)
        es = ctx.asset_metrics.get("expected_shortfall", 0)
        regime_name = ctx.regime.get("regime", "UNKNOWN").upper()
        adj_risk_pct = ctx.adjusted_risk_percent * 100

        # ── REGIME EXPLANATION ──────────────────
        regime_explanations = {
            "HIGH_VOL": (
                "HIGH VOLATILITY — The asset's recent price swings are statistically elevated. "
                "The regime engine has detected daily return dispersion above normal thresholds. "
                f"Adaptive risk allocation has been reduced to {adj_risk_pct:.1f}% of account per trade."
            ),
            "LOW_VOL": (
                "LOW VOLATILITY — The market is in a compression phase. "
                "Price action is tight and mean-reverting. "
                f"Standard allocation of {adj_risk_pct:.1f}% per trade is acceptable."
            ),
            "NORMAL_VOL": (
                "NORMAL VOLATILITY — Asset is trading within historical norms. "
                f"Risk allocation set to {adj_risk_pct:.1f}% of account per trade."
            ),
        }
        regime_text = regime_explanations.get(
            regime_name,
            f"Regime: {regime_name}. Adjusted risk allocation: {adj_risk_pct:.1f}%."
        )

        # ── ASSET RISK SECTION ───────────────────
        vol_annualized = vol * (252 ** 0.5)
        es_pct = es * 100

        lines = [
            f"## INSTITUTIONAL RISK REPORT — {ticker}",
            "",
            "---",
            "",
            "### SECTION 1 — ASSET RISK PROFILE",
            "",
            f"| Metric | Raw Value | Annualized | Interpretation |",
            f"| :--- | :--- | :--- | :--- |",
            f"| Daily Volatility | {vol:.4f} | {vol_annualized:.4f} ({vol_annualized*100:.2f}%/yr) | {'HIGH — handle with reduced size' if vol_annualized > 0.30 else 'MODERATE — standard caution' if vol_annualized > 0.15 else 'LOW — stable asset'} |",
            f"| Expected Shortfall (CVaR) | {es:.4f} | — | On your worst 5% of trading days, expect to lose at least {es_pct:.2f}% of the position value |",
            f"| Risk Score (0–1) | {risk_score:.4f} | — | {'> 0.6 = High intrinsic risk' if risk_score > 0.6 else '0.3-0.6 = Moderate' if risk_score > 0.3 else '< 0.3 = Low'} |",
            f"| Composite Risk Label | — | — | {ctx.summary_label} |",
            "",
            "**Daily Volatility explained:** A daily vol of {:.4f} means the asset moves roughly {:.2f}% per day on average (1 standard deviation). ".format(vol, vol * 100)
            + "Annualized, this implies your position value could swing by {:.2f}% over a full year within normal market conditions.".format(vol_annualized * 100),
            "",
            "**Expected Shortfall (CVaR) explained:** This is not your average loss — it is the *expected magnitude* of loss "
            f"conditioned on being in the worst 5% of outcomes. A CVaR of {es_pct:.2f}% means: "
            f"in a tail-risk scenario, you should plan for losing at least {es_pct:.2f}% of the position in a single session.",
            "",
            "---",
            "",
            "### SECTION 2 — MARKET REGIME",
            "",
            regime_text,
            "",
        ]

        # ── TRADE SECTION ────────────────────────
        if ctx.trade and "error" not in ctx.trade:
            t = ctx.trade
            rr = t.get("risk_reward_ratio", 0)
            pos_size = t.get("position_size", 0)
            exposure = t.get("total_exposure", 0)
            entry = t.get("entry_price", 0)
            stop = t.get("stop_loss", 0)
            take = t.get("take_profit", 0)
            dollar_risk = (entry - stop) * pos_size if entry and stop and pos_size else 0
            dollar_reward = (take - entry) * pos_size if take and entry and pos_size else 0

            if rr < 2:
                rr_quality = "POOR — below the institutional minimum of 2.0"
                rr_action = "Do not take this trade at current levels. Widen take profit or tighten stop loss."
            elif rr < 3:
                rr_quality = "ACCEPTABLE — meets minimum threshold"
                rr_action = "Proceed with caution. Tightening stop loss or widening take profit would improve quality."
            else:
                rr_quality = "STRONG — exceeds institutional standard"
                rr_action = "Trade setup is structurally sound at current levels."

            # Break-even win rate from RR
            breakeven_wr = (1 / (1 + rr)) * 100

            lines += [
                "---",
                "",
                "### SECTION 3 — TRADE ARCHITECTURE",
                "",
                "| Parameter | Value |",
                "| :--- | :--- |",
                f"| Entry Price | USD {entry:,.2f} |",
                f"| Stop Loss | USD {stop:,.2f} |",
                f"| Take Profit | USD {take:,.2f} |",
                f"| Position Size | {pos_size} shares |",
                f"| Total Exposure | USD {exposure:,.2f} |",
                f"| Dollar Risk (max loss) | USD {dollar_risk:,.2f} |",
                f"| Dollar Reward (max gain) | USD {dollar_reward:,.2f} |",
                f"| Risk/Reward Ratio | {rr:.2f} |",
                f"| Trade Quality | {rr_quality} |",
                "",
                # Replace the Position Size paragraph
                f"**Position size explained:** The model calculated {pos_size} shares based on your account size and the "
                f"distance between entry (USD {entry:,.2f}) and stop loss (USD {stop:,.2f}). "
                f"This ensures maximum downside exposure of USD {dollar_risk:,.2f} if the stop is hit.",
                "",
                # Replace the Risk/Reward paragraph
                f"**Risk/Reward ({rr:.2f}) explained:** You are risking USD {dollar_risk:,.2f} to potentially make USD {dollar_reward:,.2f}. "
                f"With a {rr:.2f} R:R ratio, you only need to win {breakeven_wr:.1f}% of your trades to break even over a large sample. "
                f"{rr_action}",
                "",
            ]

            # ── MONTE CARLO SECTION ──────────────
            if ctx.capital:
                survival = ctx.capital.get("survival_rate", None)
                avg_dd = ctx.capital.get("avg_drawdown", None)
                median_final = ctx.capital.get("median_final_capital", None)
                ruin_prob = ctx.capital.get("ruin_probability", None)
                n_trades = 50
                account = t.get("account_size", ctx.capital.get("initial_capital", 100000))

                # survival_rate and ruin_probability come from CapitalSimulator as 0–1 floats
                survival_str = f"{survival * 100:.1f}%" if survival is not None else "not computed"
                avg_dd_str = f"{avg_dd * 100:.2f}%" if avg_dd is not None else "not computed"
                median_str = f"USD {median_final:,.2f}" if median_final is not None else "not computed"
                ruin_str = f"{ruin_prob * 100:.2f}%" if ruin_prob is not None else "not computed"

                lines += [
                    "---",
                    "",
                    "### SECTION 4 — MONTE CARLO CAPITAL SIMULATION (300 paths, 50 trades)",
                    "",
                    "| Metric | Value | What It Means |",
                    "| :--- | :--- | :--- |",
                    f"| Survival Rate | {survival_str} | Percentage of simulated 50-trade sequences that did NOT hit ruin |",
                    f"| Average Max Drawdown | {avg_dd_str} | Average worst-case peak-to-trough decline across all 300 paths |",
                    f"| Median Final Capital | {median_str} | The midpoint outcome — 50% of simulations ended above this value |",
                    f"| Ruin Probability | {ruin_str} | Probability of losing enough capital to be unable to continue trading |",
                    "",
                    f"**Simulation context:** 300 independent paths were simulated, each running {n_trades} sequential trades "
                    f"using {ticker}'s historical return distribution and the current market regime ({regime_name}). "
                    f"Starting capital for each path: ${account:,.2f}.",
                    "",
                ]
                if avg_dd is not None:
                    dd_dollar = account * avg_dd
                    lines.append(
                        f"**Drawdown in dollar terms:** An average max drawdown of {avg_dd_str} on a ${account:,.2f} account "
                        f"translates to an expected worst-case decline of approximately ${dd_dollar:,.2f} during a losing streak."
                    )
                    lines.append("")
            else:
                lines += [
                    "---",
                    "",
                    "### SECTION 4 — MONTE CARLO CAPITAL SIMULATION",
                    "",
                    "Simulation not computed — capital input was not provided.",
                    "",
                ]

        elif ctx.trade and "error" in ctx.trade:
            lines += [
                "---",
                "",
                "### SECTION 3 — TRADE ARCHITECTURE",
                "",
                f"ERROR: {ctx.trade['error']}",
                "",
            ]
        else:
            # No trade input — asset-only report
            lines += [
                "---",
                "",
                "### SECTION 3 — TRADE ARCHITECTURE",
                "",
                "No trade parameters provided. Supply entry price, stop loss, and take profit for a full trade evaluation.",
                "",
            ]

        # ── RECOMMENDATION ───────────────────────
        lines += [
            "---",
            "",
            "### SECTION 5 — RECOMMENDATION",
            "",
            f"**Engine output:** {ctx.recommendation}",
            "",
            f"**Overall risk classification:** {ctx.summary_label} (composite score: {ctx.summary_score:.4f})",
            "",
            "*Composite score is weighted: 40% asset volatility, 20% forecast risk, 10% capital survival. "
            "Scores below 0.02 = Low Risk. 0.02-0.05 = Moderate. Above 0.05 = High.*",
        ]

        return "\n".join(lines)