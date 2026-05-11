# FinanceBot — AI Financial Intelligence System

A production-grade quantitative finance terminal built on a PyTorch Temporal Fusion Transformer for stock direction forecasting, an institutional risk analysis pipeline with regime detection and Monte Carlo simulation, and a LangChain-powered conversational agent for trade and portfolio evaluation.

---

## Overview

FinanceBot is a multi-component AI system designed for quantitative financial analysis. It integrates a trained deep learning forecasting model with a statistical risk engine, exposing both through a natural language interface built on a structured single-shot agent pipeline.

The system is built around three independently functioning modules:

- **TFT Forecasting Engine** — a macro-enabled Temporal Fusion Transformer that predicts next-day price direction and magnitude from 30+ engineered features
- **Institutional Risk Pipeline** — computes volatility, CVaR, market regime, position sizing, risk/reward, and capital survival probability via Monte Carlo simulation
- **LangChain Agent** — routes user queries to the correct tool in a single-shot pipeline that structurally cannot loop, then returns formatted reports verbatim

---

## Architecture

```
User Query (Streamlit UI)
        |
   run_agent()
        |
   _classify()  ──── greeting / theoretical ──── plain LLM response
        |
   actionable
        |
   LLM tool selection (llm_with_tools)
        |
   Single tool execution (TOOL_MAP)
        |
   ┌─────────────────────────────────────────────┐
   │  get_stock_price         │  yfinance live    │
   │  predict_stock_direction │  TFT model        │
   │  comprehensive_risk_analysis │ RiskService   │
   │  analyze_full_portfolio  │  PortfolioRisk    │
   └─────────────────────────────────────────────┘
        |
   Formatted Markdown report returned directly
        |
   Streamlit chat UI
```

---

## Modules

### TFT Forecasting Engine (`core/tft_service.py`)

- Architecture: Temporal Fusion Transformer loaded from a pre-trained checkpoint (`tft_Fold 3-v1.ckpt`)
- Hardware: CUDA-accelerated inference; falls back to CPU automatically
- Input: 150 days of historical OHLCV data for the target asset plus SPY macro features
- Feature set: 30+ engineered features including RSI, MACD, ATR, Bollinger Band position, Williams %R, Stochastic K, OBV, log returns at 6 lag periods, ROC at 3 periods, 20-day historical volatility, and SPY correlation
- Target: next-day log return (clipped at 1st/99th percentile during training)
- Output: predicted direction (UP/DOWN), predicted price, last close price, inference time in ms
- Scaling: RobustScaler fitted at inference time on the same feature set used during training
- Time encoding: cyclical sine/cosine encoding for day-of-week and month

### Institutional Risk Pipeline (`core/risk_service.py`)

The `full_analysis` method runs a 9-stage pipeline:

| Stage | Module | Output |
|:---|:---|:---|
| Asset Risk | `RiskSentinel` | Volatility, CVaR, risk score (0-1) |
| Regime Detection | `RegimeEngine` | high\_vol / normal\_vol / low\_vol |
| Adaptive Risk | `RegimeEngine` | Risk % adjusted to current regime |
| Forecast Risk | `ForecastRiskEngine` | Integrated forecast risk score |
| Trade Analysis | `TradeRiskEngine` | Position size, exposure, R:R ratio |
| Capital Simulation | `CapitalSimulator` | 300-path Monte Carlo over 50 trades |
| Composite Score | weighted sum | 40% asset vol + 20% forecast + 10% capital |
| Risk Label | threshold | Low / Moderate / High |
| Report | `_build_report` | Full formatted Markdown output |

**Position sizing formula:**

```
risk_amount = account_size * regime_adjusted_risk_percent
position_size = floor(risk_amount / (entry_price - stop_loss))
```

**Monte Carlo simulation:** 300 independent paths, each simulating 50 sequential trades drawn from the asset's historical return distribution under the detected market regime. Outputs: survival rate, average max drawdown, median final capital, ruin probability.

**Composite risk score:**
```
score = 0.4 * asset_risk_score + 0.2 * forecast_risk + 0.1 * (1 - avg_drawdown)
```

### Portfolio Risk (`core/portfolio.py`, `core/risk_decomposition.py`)

- Fetches 1 year of daily close prices for all holdings via yfinance
- Computes annualized covariance matrix (daily cov * 252)
- Portfolio volatility via matrix multiplication: `sqrt(w^T * Sigma * w)`
- Diversification benefit: `(weighted_avg_individual_vol - portfolio_vol) / weighted_avg_individual_vol`
- Outputs: annualized volatility, 1-SD and 2-SD dollar risk bands, diversification benefit with classification

### Agent Pipeline (`agent.py`)

Replaces LangGraph's `create_react_agent` with a structurally loop-free three-step pipeline:

```python
Step 1 — _classify(message)
         'greeting'    -> static response, 0 LLM calls
         'theoretical' -> plain LLM call, 0 tool calls
         'actionable'  -> proceed to Step 2

Step 2 — llm_with_tools.invoke(messages)
         LLM selects one tool and returns tool_calls[0]

Step 3 — TOOL_MAP[name].invoke(args)
         Tool executes once, result returned directly
         No LLM reformatting step — prevents hallucination
```

The plain `llm` (used in Step 1b) has no tools bound. The tool execution in Step 3 bypasses the LLM entirely for formatted reports. This eliminates the infinite tool-calling loop that occurs with ReAct agents when the LLM repeatedly re-evaluates tool results.

---

## Tech Stack

| Layer | Technology |
|:---|:---|
| Forecasting model | PyTorch, pytorch-forecasting (TFT) |
| ML features | ta (technical analysis), scikit-learn (RobustScaler) |
| Market data | yfinance |
| LLM | Llama 3.3 70B via Groq API |
| Agent framework | LangChain (tool binding, message types) |
| UI | Streamlit |
| Risk computation | NumPy, Pandas |
| Python | 3.10+ |

---

## Project Structure

```
├── app.py                           # Streamlit UI
├── agent.py                         # Single-shot agent pipeline and tool definitions
├── tft_Fold 3-v1.ckpt              # Pre-trained TFT model checkpoint
├── core/
│   ├── tft_service.py              # TFT inference pipeline
│   ├── risk_service.py             # Full risk analysis orchestrator
│   ├── risk_sentinel.py            # Asset volatility and CVaR computation
│   ├── regime_engine.py            # Market regime detection
│   ├── trade_risk.py               # Position sizing and R:R calculation
│   ├── capital_simulator.py        # Monte Carlo capital simulation
│   ├── portfolio.py                # Portfolio volatility computation
│   ├── risk_decomposition.py       # Marginal risk contribution
│   ├── forecast_risk.py            # Forecast-integrated risk scoring
│   ├── recommender.py              # Rule-based recommendation engine
│   ├── explainer.py                # Report text generation
│   ├── context.py                  # RiskContext dataclass
│   ├── walk_forward_tft.ipynb      # Walk-forward TFT training pipeline
│   └── walk_forward_tft_testing.ipynb # TFT walk-forward evaluation/testing
│
├──filtered_broad_news.csv
├──filtered_company_news.csv
├──Financial_Categorized.csv
├──financial_kb.json
├──financial_sentiment.ipynb
├──stock_market_final_30_macro.csv
└── requirements.txt
```

---

## Setup

**Prerequisites:** Python 3.10+, CUDA-capable GPU recommended (CPU inference supported)

```bash
git clone https://github.com/namitpatel3006/financebot
cd financebot

conda create -n tft_env python=3.10
conda activate tft_env

pip install -r requirements.txt
```

Set your Groq API key:

```bash
# Windows
set GROQ_API_KEY=your_key_here

# Linux / macOS
export GROQ_API_KEY=your_key_here
```

Place the model checkpoint in the project root:
```
tft_Fold 3-v1.ckpt
```

Run the application:
```bash
python -m streamlit run app.py
```

---

## Usage

The interface accepts natural language queries. Examples:

```
What is NVDA's current price?
Predict tomorrow's direction for AAPL
Risk: TSLA, $50k account, entry $170, stop $160, target $195
Portfolio: NVDA:15000, MSFT:10000, GLD:5000
What is CVaR?
```

For trade risk analysis, the agent requires three parameters: ticker, entry price, and stop loss. If any are missing it will ask before calling the tool. Take profit is optional and defaults to entry * 1.10.

---

## Sample Output

**Price quote:**
```
NVDA  |  USD 213.17  |  prev close USD 216.61  |  -1.59% today
```

**TFT forecast:**
```
Predicted Direction : UP
Predicted Price     : USD 274.50
Last Close          : USD 270.71
Inference Time      : 847 ms
```

**Risk report sections:**
- Section 1: Daily volatility, annualized volatility, CVaR, risk score, composite label
- Section 2: Market regime with adaptive risk allocation percentage
- Section 3: Position size, total exposure, dollar risk, dollar reward, R:R ratio
- Section 4: Monte Carlo survival rate, average max drawdown, median final capital, ruin probability
- Section 5: Engine recommendation and composite score breakdown

---

## Model Training Notes

The TFT model was trained using k-fold cross-validation. The checkpoint included (`tft_Fold 3-v1.ckpt`) is the best-performing fold by validation loss. Training features include SPY macro features (log return, 20-day rolling volatility) merged with per-asset OHLCV and 30+ technical indicators. The target variable is the next-day log return, clipped at the 1st and 99th percentile to reduce the influence of outlier sessions.

Inference replicates the training preprocessing pipeline exactly: RobustScaler fitted on the same UNKNOWN_REALS feature list, cyclical time encoding, and GroupNormalizer as the target normalizer.

---

## Limitations

- The TFT model predicts return direction and magnitude for the next trading day only. It does not produce multi-step forecasts.
- Predictions are probabilistic model outputs, not financial advice.
- The Groq free tier has a 100,000 token per day limit. Heavy usage will hit this limit.
- Monte Carlo simulation uses historical return distributions. It does not model structural breaks or regime changes mid-simulation.
- yfinance data may be delayed up to 15 minutes during market hours.

---
