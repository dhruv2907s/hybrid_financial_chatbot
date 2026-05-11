import os
import json
import traceback
import pandas as pd
import yfinance as yf
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from core.risk_service import RiskService
from core.tft_service import TFTService

risk_service = RiskService()
tft_service = TFTService(model_path="tft_Fold 3-v1.ckpt")

# ──────────────────────────────────────────────
# TOOLS
# ──────────────────────────────────────────────

@tool
def get_stock_price(ticker: str) -> str:
    """Fetch the current price of a stock. Returns a formatted markdown report."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if hist.empty:
            return f"ERROR: No data returned for {ticker.upper()}."
        current = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
        change = current - prev
        change_pct = (change / prev) * 100
        direction = "+" if change >= 0 else ""

        return (
            f"## PRICE QUOTE — {ticker.upper()}\n\n"
            f"| Metric | Value |\n"
            f"| :--- | :--- |\n"
            f"| Current Price | USD {current:,.2f} |\n"
            f"| Previous Close | USD {prev:,.2f} |\n"
            f"| Day Change | {direction}{change:,.2f} ({direction}{change_pct:.2f}%) |\n\n"
            f"*Data sourced via yfinance. Prices may be delayed up to 15 minutes.*"
        )
    except Exception as e:
        return f"ERROR: Could not fetch price for {ticker}: {str(e)}"


@tool
def predict_stock_direction(ticker: str) -> str:
    """
    Forecast tomorrow's price using the integrated PyTorch TFT model.
    Returns a formatted markdown report with predicted direction and price.
    """
    print(f"\n[SYSTEM] Running TFT inference for {ticker}...")
    result = tft_service.predict_direction(ticker)

    if "error" in result:
        return f"## TFT FORECAST — {ticker.upper()}\n\nERROR: {result['error']}"

    print(f"[SYSTEM] TFT inference complete in {result.get('inference_time_ms')}ms.")

    t = ticker.upper()
    direction = result.get("predicted_direction", "UNKNOWN")
    pred_price = result.get("predicted_price", 0)
    last_close = result.get("last_close_price", 0)
    inf_time = result.get("inference_time_ms", 0)
    delta = pred_price - last_close
    delta_pct = (delta / last_close * 100) if last_close else 0
    sign = "+" if delta >= 0 else ""

    return (
        f"## TFT FORECAST — {t}\n\n"
        f"| Metric | Value |\n"
        f"| :--- | :--- |\n"
        f"| Last Close Price | USD {last_close:,.2f} |\n"
        f"| Predicted Price (tomorrow) | USD {pred_price:,.2f} |\n"
        f"| Predicted Change | {sign}{delta:,.2f} ({sign}{delta_pct:.2f}%) |\n"
        f"| Predicted Direction | {direction} |\n"
        f"| Inference Time | {inf_time} ms |\n\n"
        f"**Model:** PyTorch Temporal Fusion Transformer (TFT) — macro-enabled, trained on 1-year lookback.\n\n"
        f"**Note:** This is a quantitative model output. Predicted price reflects the median quantile of the "
        f"model's return distribution applied to the last closing price. Not financial advice."
    )


@tool
def comprehensive_risk_analysis(
    ticker: str,
    account_size: float = 100000.0,
    entry_price: float = 0.0,
    stop_loss: float = 0.0,
    take_profit: float = 0.0,
) -> str:
    """
    Institutional risk analysis: volatility, regime detection, position sizing, Monte Carlo.
    Returns a fully formatted Markdown report.
    """
    print(f"\n[SYSTEM] Running risk analysis for {ticker}...")

    def clean(val):
        if not val or val == 0.0:
            return None
        if isinstance(val, str):
            return float(val.replace("$", "").replace(",", "").strip())
        return float(val)

    try:
        c_account = clean(account_size) or 100000.0
        c_entry = clean(entry_price)
        c_stop = clean(stop_loss)
        c_take = clean(take_profit)

        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty:
            return f"ERROR: No historical data for {ticker}."
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        price_series = df["Close"].dropna()

        # 🔥 GET CURRENT PRICE FOR AUTO-FILL
        current_price = float(price_series.iloc[-1])

        # 🔥 AUTO-FILL MISSING INPUTS
        c_entry = c_entry if c_entry else current_price
        c_stop = c_stop if c_stop else (c_entry * 0.95) # Default 5% stop loss
        c_take = c_take if c_take else (c_entry * 1.10) # Default 10% take profit

        trade_input = {
            "entry_price": c_entry,
            "stop_loss": c_stop,
            "take_profit": c_take,
            "account_size": c_account,
        }

        capital_input = {
            "initial_capital": c_account,
            "n_trades": 50,
            "simulations": 300,
        }

        ctx = risk_service.full_analysis(
            ticker=ticker,
            price_series=price_series,
            trade_input=trade_input,
            capital_input=capital_input,
        )
        return ctx.explanation

    except Exception:
        traceback.print_exc()
        return f"Risk analysis failed for {ticker}."


@tool
def analyze_full_portfolio(portfolio_query: str) -> str:
    """
    Portfolio risk analysis. Input: comma-separated 'TICKER:AMOUNT' pairs.
    Example: 'AAPL:5000, TSLA:2000, GLD:1000'
    """
    try:
        holdings = {}
        for item in portfolio_query.replace("\n", ",").replace('"', "").split(","):
            if ":" in item:
                ticker, amount = item.split(":", 1)
                t = ticker.strip().upper()
                a = amount.replace("$", "").replace(",", "").strip()
                if t and a:
                    holdings[t] = float(a)

        if not holdings:
            return "ERROR: Could not parse portfolio. Use format 'AAPL:5000, TSLA:2000'."

        print(f"\n[SYSTEM] Analyzing portfolio: {holdings}")
        result = risk_service.analyze_portfolio_basket(holdings)

        total_value = result["total_value"]
        vol_pct = result["annual_volatility"]
        dollar_vol = total_value * vol_pct
        benefit_pct = result["diversification_benefit"]
        tickers = result["tickers"]

        vol_label = (
            "CONSERVATIVE — below 12%, low price swings"
            if vol_pct < 0.12
            else "MODERATE — between 12-20%, normal equity range"
            if vol_pct < 0.20
            else "HIGH-RISK — above 20%, significant price swings expected"
        )
        div_label = (
            "WEAK — assets are highly correlated, diversification adds little"
            if benefit_pct < 0.05
            else "MODERATE — partial correlation reduction achieved"
            if benefit_pct < 0.10
            else "STRONG — meaningful volatility reduction from asset mix"
        )

        # Use USD prefix everywhere to avoid Streamlit's LaTeX $ parser
        low_band = total_value - dollar_vol
        high_band = total_value + dollar_vol
        low_band_2sd = total_value - 2 * dollar_vol
        high_band_2sd = total_value + 2 * dollar_vol

        alloc_rows = "\n".join(
            f"| {t} | USD {holdings[t]:,.2f} | {(holdings[t]/total_value)*100:.1f}% |"
            for t in tickers
        )

        return (
            f"## PORTFOLIO RISK REPORT\n\n"
            f"### ALLOCATION\n"
            f"| Ticker | Dollar Value | Weight |\n"
            f"| :--- | ---: | ---: |\n"
            f"{alloc_rows}\n"
            f"| **TOTAL** | **USD {total_value:,.2f}** | **100%** |\n\n"
            f"### KEY METRICS\n"
            f"| Metric | Value | Interpretation |\n"
            f"| :--- | :--- | :--- |\n"
            f"| Annualized Volatility | {vol_pct*100:.2f}% | {vol_label} |\n"
            f"| 1-Year Dollar Risk (1 SD, 68% CI) | USD {dollar_vol:,.2f} | "
            f"Portfolio value will fall within USD {low_band:,.2f} to USD {high_band:,.2f} with 68% probability |\n"
            f"| 2-Year Dollar Risk (2 SD, 95% CI) | USD {2*dollar_vol:,.2f} | "
            f"Worst-case band: USD {low_band_2sd:,.2f} to USD {high_band_2sd:,.2f} |\n"
            f"| Diversification Benefit | {benefit_pct*100:.2f}% | {div_label} |\n\n"
            f"### INTERPRETATION\n"
            f"Holding these {len(tickers)} assets together instead of a single concentrated position "
            f"has mathematically reduced portfolio volatility by **{benefit_pct*100:.2f}%** "
            f"relative to the weighted average of each asset's standalone volatility. "
            f"A benefit above 10% is considered institutionally meaningful.\n\n"
            f"At {vol_pct*100:.2f}% annualized volatility, a 1-standard-deviation move over 12 months "
            f"implies your total portfolio value could shift by up to USD {dollar_vol:,.2f}. "
            f"The 95% confidence interval is approximately double that range."
        )

    except Exception as e:
        traceback.print_exc()
        return f"Portfolio analysis failed: {str(e)}"


# ──────────────────────────────────────────────
# TOOL REGISTRY
# ──────────────────────────────────────────────

ALL_TOOLS = [
    get_stock_price,
    predict_stock_direction,
    comprehensive_risk_analysis,
    analyze_full_portfolio,
]

TOOL_MAP = {t.name: t for t in ALL_TOOLS}

# Tools that return pre-formatted markdown — skip LLM Step 3, pass through directly
PASSTHROUGH_TOOLS = {
    "comprehensive_risk_analysis",
    "analyze_full_portfolio",
    "get_stock_price",
    "predict_stock_direction",
}

# ──────────────────────────────────────────────
# LLM
# ──────────────────────────────────────────────

os.environ["GROQ_API_KEY"] = os.getenv("")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
llm_with_tools = llm.bind_tools(ALL_TOOLS)

# Greetings and off-topic messages — handle without touching a tool
GREETING_TOKENS = {
    "hi", "hello", "hey", "yo", "sup", "howdy", "greetings",
    "good morning", "good afternoon", "good evening",
    "what can you do", "help", "what are you", "who are you",
}

# SYSTEM_PROMPT = """You are FinanceBot — a quantitative risk terminal.

# Available tools:
# - get_stock_price       → live price quote for a ticker
# - predict_stock_direction → TFT model: tomorrow's price and direction
# - comprehensive_risk_analysis → full trade risk report (needs entry, stop, account size)
# - analyze_full_portfolio → portfolio volatility + diversification (needs ticker:amount pairs)

# RULES:
# 1. Call exactly ONE tool per request.
# 2. Never call a tool for greetings, meta-questions, or anything that does not name a specific ticker.
# 3. The tool already formats its output. Output the tool result VERBATIM — zero modifications.
# 4. Never fabricate numbers. If a tool fails, report the error exactly as returned."""
SYSTEM_PROMPT = """You are FinanceBot — a quantitative risk terminal and financial educator.

Available tools:
- get_stock_price       → live price quote for a ticker
- predict_stock_direction → TFT model: tomorrow's price and direction
- comprehensive_risk_analysis → full trade risk report (needs entry, stop, account size)
- analyze_full_portfolio → portfolio volatility + diversification (needs ticker:amount pairs)

RULES:
1. Call exactly ONE tool if the user provides a ticker or portfolio.
2. If the user asks a theoretical or educational question about finance (e.g., "what is risk", "how does monte carlo work"), answer it directly and professionally using your internal knowledge. Do NOT call a tool. Use markdown formatting to make your explanation readable.
3. When using a tool, the tool already formats its output. Output the tool result VERBATIM — zero modifications.
4. Never fabricate numbers. If a tool fails, report the error exactly as returned."""


# ──────────────────────────────────────────────
# SINGLE-SHOT AGENT — structurally cannot loop
# ──────────────────────────────────────────────

def _is_greeting(text: str) -> bool:
    """Return True only if the message is a direct greeting."""
    normalized = text.lower().strip().rstrip("!?.,")
    # Only block exact matches to our greeting list
    if normalized in GREETING_TOKENS:
        return True
    return False


GREETING_RESPONSE = (
    "**FinanceBot — Quantitative Risk Engine**\n\n"
    "Connected to: PyTorch TFT model · institutional risk pipeline · live market data.\n\n"
    "| Capability | Example query |\n"
    "| :--- | :--- |\n"
    "| Live price | `What is NVDA's price?` |\n"
    "| Forecast | `Predict tomorrow's direction for AAPL` |\n"
    "| Trade risk | `Risk: TSLA, $50k account, entry $170, stop $160, target $195` |\n"
    "| Portfolio | `Portfolio: NVDA:15000, MSFT:10000, GLD:5000` |\n\n"
    "Provide a ticker and query to begin."
)


def run_agent(user_message: str) -> str:
    """
    Three-step pipeline. Structurally cannot loop.

    Step 1 — Greeting check (no LLM call needed).
    Step 2 — Ask LLM which tool to call.
    Step 3 — Execute that ONE tool and return the result directly (no LLM reformatting).
    """

    # ── STEP 1: Greeting guard ────────────────
    if _is_greeting(user_message):
        print("[AGENT] Greeting detected — skipping tool call.")
        return GREETING_RESPONSE

    # ── STEP 2: Tool selection ────────────────
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    print("\n[AGENT] Step 2 — requesting tool selection from LLM...")
    ai_msg = llm_with_tools.invoke(messages)

    # LLM answered without a tool (clarification, error, etc.)
    if not ai_msg.tool_calls:
        print("[AGENT] No tool call — returning LLM direct answer.")
        return ai_msg.content

    # ── STEP 3: Execute exactly ONE tool ─────
    call = ai_msg.tool_calls[0]   # hard-cap: ignore any extras
    name = call["name"]
    args = call["args"]

    print(f"[AGENT] Step 3 — executing {name}({args})")

    if name not in TOOL_MAP:
        return f"**Error:** Unknown tool `{name}` was requested."

    try:
        raw = TOOL_MAP[name].invoke(args)
        # All tools now return pre-formatted strings — pass through directly
        return str(raw)
    except Exception as e:
        traceback.print_exc()
        return f"**Tool execution failed:** `{str(e)}`"