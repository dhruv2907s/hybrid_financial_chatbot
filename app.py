# import streamlit as st
# from agent import run_agent

# # ──────────────────────────────────────────────
# # PAGE CONFIG
# # ──────────────────────────────────────────────
# st.set_page_config(
#     page_title="FinanceBot — Quantitative Risk Engine",
#     page_icon="",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # ──────────────────────────────────────────────
# # GLOBAL CSS
# # ──────────────────────────────────────────────
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

# html, body, [data-testid="stAppViewContainer"] {
#     background-color: #0a0c0f !important;
#     color: #c8cdd6 !important;
#     font-family: 'IBM Plex Sans', sans-serif;
# }

# [data-testid="stHeader"] { background: transparent; }
# [data-testid="stSidebar"] {
#     background-color: #0d1017 !important;
#     border-right: 1px solid #1e2530 !important;
# }

# h1, h2, h3, h4 {
#     font-family: 'IBM Plex Mono', monospace !important;
#     letter-spacing: -0.02em;
# }

# .sidebar-label {
#     font-family: 'IBM Plex Mono', monospace;
#     font-size: 10px;
#     font-weight: 600;
#     color: #4a90d9;
#     letter-spacing: 0.15em;
#     text-transform: uppercase;
#     margin: 20px 0 8px 0;
#     padding-bottom: 6px;
#     border-bottom: 1px solid #1e2530;
# }

# .chip {
#     background: #111820;
#     border: 1px solid #1e2530;
#     border-radius: 4px;
#     padding: 8px 12px;
#     margin-bottom: 6px;
#     font-size: 12px;
#     color: #8a9bb0;
#     font-family: 'IBM Plex Mono', monospace;
# }

# .chip-title {
#     color: #4a90d9;
#     font-size: 10px;
#     text-transform: uppercase;
#     letter-spacing: 0.1em;
#     display: block;
#     margin-bottom: 2px;
# }

# .user-bubble {
#     background: #111820;
#     border: 1px solid #1e2530;
#     border-left: 3px solid #4a90d9;
#     border-radius: 0 6px 6px 0;
#     padding: 14px 18px;
#     margin: 12px 0;
#     font-size: 14px;
#     color: #c8cdd6;
# }

# .bot-bubble {
#     background: #0d1017;
#     border: 1px solid #1e2530;
#     border-radius: 6px;
#     padding: 20px 24px;
#     margin: 12px 0;
#     font-size: 13px;
#     line-height: 1.75;
#     color: #b8c2d0;
# }

# /* Tables */
# .bot-bubble table {
#     width: 100%;
#     border-collapse: collapse;
#     font-family: 'IBM Plex Mono', monospace;
#     font-size: 12px;
#     margin: 12px 0;
# }
# .bot-bubble table th {
#     background: #161d27;
#     color: #4a90d9;
#     padding: 8px 12px;
#     text-align: left;
#     font-weight: 600;
#     letter-spacing: 0.05em;
#     border-bottom: 2px solid #1e2530;
# }
# .bot-bubble table td {
#     padding: 7px 12px;
#     border-bottom: 1px solid #141b24;
#     color: #a0aabb;
# }
# .bot-bubble table tr:last-child td { border-bottom: none; }
# .bot-bubble table tr:hover td { background: #111820; }

# /* Headings inside bot bubble */
# .bot-bubble h2 {
#     font-size: 14px !important;
#     color: #e0e6f0 !important;
#     border-bottom: 1px solid #1e2530;
#     padding-bottom: 8px;
#     margin: 4px 0 16px 0;
# }
# .bot-bubble h3 {
#     font-size: 11px !important;
#     color: #4a90d9 !important;
#     text-transform: uppercase;
#     letter-spacing: 0.12em;
#     margin: 20px 0 10px 0;
# }
# .bot-bubble hr {
#     border: none;
#     border-top: 1px solid #1a2230;
#     margin: 16px 0;
# }
# .bot-bubble strong { color: #dde3ee; }
# .bot-bubble code {
#     background: #161d27;
#     color: #7ec8e3;
#     padding: 1px 5px;
#     border-radius: 3px;
#     font-family: 'IBM Plex Mono', monospace;
#     font-size: 12px;
# }

# /* Thinking bar */
# .thinking {
#     display: flex;
#     align-items: center;
#     gap: 10px;
#     padding: 12px 16px;
#     background: #0d1017;
#     border: 1px solid #1e2530;
#     border-radius: 6px;
#     font-family: 'IBM Plex Mono', monospace;
#     font-size: 12px;
#     color: #4a90d9;
#     margin: 8px 0;
# }
# .dot {
#     width: 7px; height: 7px;
#     border-radius: 50%;
#     background: #4a90d9;
#     animation: blink 1.1s ease-in-out infinite;
# }
# @keyframes blink {
#     0%, 100% { opacity: 1; }
#     50% { opacity: 0.2; }
# }

# /* Chat input */
# [data-testid="stChatInput"] textarea {
#     background-color: #0d1017 !important;
#     border: 1px solid #1e2530 !important;
#     border-radius: 6px !important;
#     color: #c8cdd6 !important;
#     font-family: 'IBM Plex Sans', sans-serif !important;
#     font-size: 14px !important;
#     caret-color: #4a90d9;
# }
# [data-testid="stChatInput"] textarea:focus {
#     border-color: #4a90d9 !important;
#     box-shadow: 0 0 0 1px #4a90d9 !important;
# }

# /* Buttons */
# .stButton > button {
#     background: #111820 !important;
#     border: 1px solid #1e2530 !important;
#     color: #7a8a9a !important;
#     font-family: 'IBM Plex Mono', monospace !important;
#     font-size: 11px !important;
#     border-radius: 4px !important;
#     padding: 6px 10px !important;
#     width: 100%;
#     text-align: left !important;
#     transition: all 0.15s ease;
# }
# .stButton > button:hover {
#     border-color: #4a90d9 !important;
#     color: #4a90d9 !important;
# }

# ::-webkit-scrollbar { width: 4px; }
# ::-webkit-scrollbar-track { background: #0a0c0f; }
# ::-webkit-scrollbar-thumb { background: #1e2530; border-radius: 2px; }
# #MainMenu, footer, header { visibility: hidden; }
# </style>
# """, unsafe_allow_html=True)


# # ──────────────────────────────────────────────
# # SIDEBAR
# # ──────────────────────────────────────────────
# with st.sidebar:
#     st.markdown('<div class="sidebar-label">System</div>', unsafe_allow_html=True)
#     st.markdown("""
#     <div class="chip"><span class="chip-title">Forecasting Model</span>PyTorch Temporal Fusion Transformer</div>
#     <div class="chip"><span class="chip-title">Risk Engine</span>Regime Detection + Monte Carlo (300 paths)</div>
#     <div class="chip"><span class="chip-title">LLM</span>Llama 3.3 70B via Groq</div>
#     <div class="chip"><span class="chip-title">Data</span>yfinance — live market feed</div>
#     """, unsafe_allow_html=True)

#     st.markdown('<div class="sidebar-label">Quick Queries</div>', unsafe_allow_html=True)
#     examples = [
#         "Price: NVDA",
#         "Forecast: AAPL",
#         "Risk: TSLA, $50k account, entry $170, stop $160, target $195",
#         "Portfolio: NVDA:15000, MSFT:10000, GLD:5000",
#     ]
#     for ex in examples:
#         if st.button(ex, key=ex):
#             st.session_state["prefill"] = ex

#     st.markdown("""
#     <div style="margin-top:32px; font-family:'IBM Plex Mono',monospace; font-size:10px;
#                 color:#2a3545; border-top:1px solid #1a2230; padding-top:10px;">
#         For research use only. Not financial advice.
#     </div>
#     """, unsafe_allow_html=True)


# # ──────────────────────────────────────────────
# # HEADER
# # ──────────────────────────────────────────────
# st.markdown("""
# <div style="padding:28px 0 20px 0; border-bottom:1px solid #1e2530; margin-bottom:24px;">
#     <span style="font-family:'IBM Plex Mono',monospace; font-size:10px; color:#4a90d9;
#                  letter-spacing:0.15em; text-transform:uppercase;">
#         Quantitative Risk Engine
#     </span>
#     <h1 style="font-family:'IBM Plex Mono',monospace; font-size:26px; color:#e0e6f0;
#                margin:6px 0 4px 0; font-weight:600; letter-spacing:-0.03em;">
#         FinanceBot
#     </h1>
#     <span style="font-size:12px; color:#3a4a5a; font-family:'IBM Plex Mono',monospace;">
#         TFT FORECAST &nbsp;/&nbsp; REGIME DETECTION &nbsp;/&nbsp; MONTE CARLO SIMULATION
#     </span>
# </div>
# """, unsafe_allow_html=True)


# # ──────────────────────────────────────────────
# # SESSION STATE
# # ──────────────────────────────────────────────
# if "messages" not in st.session_state:
#     st.session_state.messages = [{
#         "role": "assistant",
#         "content": (
#             "**System initialized.**\n\n"
#             "Connected to: PyTorch TFT model · institutional risk pipeline · live market data.\n\n"
#             "Provide a ticker and query. For trade risk analysis, include entry price, stop loss, "
#             "and optionally a take profit target."
#         ),
#     }]


# # ──────────────────────────────────────────────
# # RENDER HISTORY
# # ──────────────────────────────────────────────
# for msg in st.session_state.messages:
#     if msg["role"] == "user":
#         st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
#     else:
#         with st.container():
#             st.markdown('<div class="bot-bubble">', unsafe_allow_html=True)
#             st.markdown(msg["content"])
#             st.markdown('</div>', unsafe_allow_html=True)


# # ──────────────────────────────────────────────
# # PREFILL FROM SIDEBAR
# # ──────────────────────────────────────────────
# prefill = st.session_state.pop("prefill", None)

# # ──────────────────────────────────────────────
# # CHAT INPUT
# # ──────────────────────────────────────────────
# user_input = st.chat_input("Ticker query, trade parameters, or portfolio holdings...")
# if prefill:
#     user_input = prefill

# if user_input:
#     st.session_state.messages.append({"role": "user", "content": user_input})
#     st.markdown(f'<div class="user-bubble">{user_input}</div>', unsafe_allow_html=True)

#     thinking = st.empty()
#     thinking.markdown(
#         '<div class="thinking"><div class="dot"></div>Pipeline running — tool executing...</div>',
#         unsafe_allow_html=True,
#     )

#     try:
#         response = run_agent(user_input)
#     except Exception as e:
#         traceback_str = str(e)
#         response = f"**Pipeline error:** `{traceback_str}`"

#     thinking.empty()

#     st.session_state.messages.append({"role": "assistant", "content": response})
#     with st.container():
#         st.markdown('<div class="bot-bubble">', unsafe_allow_html=True)
#         st.markdown(response)
#         st.markdown('</div>', unsafe_allow_html=True)

import traceback
import streamlit as st
from agent import run_agent

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="FinanceBot",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CSS — main area only, no sidebar HTML tricks
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@300;400;500;600&display=swap');

/* ── BASE ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #080b10 !important;
    color: #c4cad6 !important;
    font-family: 'Inter', sans-serif;
}

/* ── SIDEBAR — use native streamlit, just restyle ── */
[data-testid="stSidebar"] {
    background-color: #0c1018 !important;
    border-right: 1px solid #18222e !important;
}
[data-testid="stSidebar"] * {
    font-family: 'Inter', sans-serif !important;
}
/* Sidebar text colors */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: #8a97a8 !important;
    font-size: 13px !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #c4cad6 !important;
    font-size: 14px !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {
    background: #111820 !important;
    border: 1px solid #1e2c3a !important;
    color: #7a8898 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    border-radius: 5px !important;
    padding: 8px 12px !important;
    width: 100% !important;
    text-align: left !important;
    margin-bottom: 4px !important;
    transition: all 0.15s ease;
    white-space: normal !important;
    height: auto !important;
    line-height: 1.4 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #3d78c0 !important;
    color: #6aabff !important;
    background: #0f1620 !important;
}
/* Sidebar divider */
[data-testid="stSidebar"] hr {
    border-color: #18222e !important;
    margin: 16px 0 !important;
}
/* Sidebar caption */
[data-testid="stSidebar"] .stCaption p {
    color: #3a4a5a !important;
    font-size: 11px !important;
}

/* ── HEADER ── */
[data-testid="stHeader"] { background: transparent !important; }

/* ── MAIN CHAT AREA ── */
.user-bubble {
    background: #0f1620;
    border: 1px solid #1e2c3a;
    border-left: 3px solid #3d78c0;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin: 14px 0 6px 0;
    font-size: 14px;
    color: #c4cad6;
    line-height: 1.6;
}

.bot-bubble {
    background: #0c1018;
    border: 1px solid #18222e;
    border-radius: 8px;
    padding: 22px 26px;
    margin: 6px 0 14px 0;
    font-size: 13.5px;
    line-height: 1.8;
    color: #a8b4c4;
}

/* Tables inside bot bubble */
.bot-bubble table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12.5px;
    margin: 14px 0;
    border-radius: 6px;
    overflow: hidden;
}
.bot-bubble table th {
    background: #131c28;
    color: #6aabff;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    letter-spacing: 0.04em;
    border-bottom: 2px solid #1e2c3a;
}
.bot-bubble table td {
    padding: 9px 14px;
    border-bottom: 1px solid #111820;
    color: #9aaabb;
}
.bot-bubble table tr:last-child td { border-bottom: none; }
.bot-bubble table tr:hover td { background: #0f1620; }

/* Headings inside bot bubble */
.bot-bubble h2 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 15px !important;
    color: #d8e0ee !important;
    border-bottom: 1px solid #18222e;
    padding-bottom: 10px;
    margin: 0 0 18px 0 !important;
    letter-spacing: -0.01em;
}
.bot-bubble h3 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important;
    color: #3d78c0 !important;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin: 22px 0 10px 0 !important;
}
.bot-bubble hr {
    border: none;
    border-top: 1px solid #141e28;
    margin: 18px 0;
}
.bot-bubble strong { color: #d0d8e8; }
.bot-bubble em { color: #607080; font-size: 12px; }
.bot-bubble code {
    background: #131c28;
    color: #6aabff;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
}
.bot-bubble p { margin: 8px 0; }

/* ── THINKING INDICATOR ── */
.thinking-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 18px;
    background: #0c1018;
    border: 1px solid #18222e;
    border-radius: 8px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #3d78c0;
    margin: 6px 0;
}
.dot1, .dot2, .dot3 {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #3d78c0;
}
.dot1 { animation: bounce 1.2s 0.0s ease-in-out infinite; }
.dot2 { animation: bounce 1.2s 0.2s ease-in-out infinite; }
.dot3 { animation: bounce 1.2s 0.4s ease-in-out infinite; }
@keyframes bounce {
    0%, 100% { opacity: 0.2; transform: translateY(0); }
    50% { opacity: 1; transform: translateY(-3px); }
}

/* ── CHAT INPUT ── */
[data-testid="stChatInput"] textarea {
    background-color: #0c1018 !important;
    border: 1px solid #18222e !important;
    border-radius: 8px !important;
    color: #c4cad6 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    caret-color: #3d78c0;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #3d78c0 !important;
    box-shadow: 0 0 0 2px rgba(61,120,192,0.15) !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #2a3a4a !important;
}

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer { visibility: hidden; }
[data-testid="stDeployButton"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SIDEBAR — 100% native Streamlit components
# ──────────────────────────────────────────────
with st.sidebar:

    st.markdown("### FinanceBot")
    st.caption("Quantitative risk analysis terminal")
    st.divider()

    # ── What you can ask ──
    st.markdown("**What can I ask?**")

    st.caption("GET A PRICE QUOTE")
    st.markdown("`What is NVDA's current price?`")

    st.caption("GET A FORECAST")
    st.markdown("`Predict tomorrow's direction for AAPL`")

    st.caption("ANALYZE A TRADE")
    st.markdown("`Risk: TSLA, 50k account, entry 170, stop 160, target 195`")

    st.caption("ANALYZE A PORTFOLIO")
    st.markdown("`Portfolio: NVDA:15000, MSFT:10000, GLD:5000`")

    st.divider()

    # ── Quick launch buttons ──
    st.markdown("**Quick start**")

    quick = [
        ("NVDA price",           "What is NVDA's current price?"),
        ("AAPL forecast",        "Predict tomorrow's direction for AAPL"),
        ("TSLA trade risk",      "Risk: TSLA, $50k account, entry $170, stop $160, target $195"),
        ("MSFT trade risk",      "Risk: MSFT, $100k account, entry $400, stop $390, target $425"),
        ("3-stock portfolio",    "Portfolio: NVDA:15000, MSFT:10000, GLD:5000"),
        ("4-stock portfolio",    "Portfolio: AAPL:20000, TSLA:10000, AMZN:10000, GLD:5000"),
    ]

    for label, query in quick:
        if st.button(label, key=label):
            st.session_state["prefill"] = query

    st.divider()

    # ── Tips ──
    st.markdown("**Tips**")
    st.caption(
        "For trade risk, always include:\n"
        "• Ticker (e.g. TSLA)\n"
        "• Account size (e.g. 50k)\n"
        "• Entry price\n"
        "• Stop loss\n"
        "• Take profit (optional)"
    )

    st.divider()
    st.caption("For research use only. Not financial advice.")


# ──────────────────────────────────────────────
# MAIN HEADER
# ──────────────────────────────────────────────
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("""
    <div style="padding: 20px 0 16px 0; border-bottom: 1px solid #18222e; margin-bottom: 20px;">
        <div style="font-family:'IBM Plex Mono',monospace; font-size:10px; color:#3d78c0;
                    letter-spacing:0.16em; text-transform:uppercase; margin-bottom:6px;">
            Risk Terminal
        </div>
        <div style="font-family:'IBM Plex Mono',monospace; font-size:28px; font-weight:600;
                    color:#e0e8f8; letter-spacing:-0.03em; line-height:1.1;">
            FinanceBot
        </div>
        <div style="font-size:12px; color:#2e4256; margin-top:5px; font-family:'IBM Plex Mono',monospace;">
            FORECAST &nbsp;·&nbsp; REGIME DETECTION &nbsp;·&nbsp; MONTE CARLO
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_status:
    st.markdown("""
    <div style="padding: 20px 0 16px 0; display:flex; flex-direction:column;
                align-items:flex-end; gap:6px; border-bottom:1px solid #18222e; margin-bottom:20px;">
        <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:7px;height:7px;border-radius:50%;background:#2ecc71;
                        box-shadow:0 0 6px #2ecc71;"></div>
            <span style="font-family:'IBM Plex Mono',monospace; font-size:11px; color:#3a5a3a;">
                TFT Model Online
            </span>
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:7px;height:7px;border-radius:50%;background:#2ecc71;
                        box-shadow:0 0 6px #2ecc71;"></div>
            <span style="font-family:'IBM Plex Mono',monospace; font-size:11px; color:#3a5a3a;">
                Risk Engine Online
            </span>
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:7px;height:7px;border-radius:50%;background:#2ecc71;
                        box-shadow:0 0 6px #2ecc71;"></div>
            <span style="font-family:'IBM Plex Mono',monospace; font-size:11px; color:#3a5a3a;">
                Live Data Online
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            "**Ready.**\n\n"
            "Ask me about any publicly traded stock. Here's what I can do:\n\n"
            "| Query type | What you get |\n"
            "| :--- | :--- |\n"
            "| **Price quote** | Current price, previous close, day change |\n"
            "| **Forecast** | Tomorrow's predicted direction and price from the TFT model |\n"
            "| **Trade risk** | Position sizing, risk/reward, Monte Carlo survival rate |\n"
            "| **Portfolio** | Annualized volatility, diversification benefit, dollar risk bands |\n\n"
            "Use the quick-start buttons in the sidebar, or type a query below."
        ),
    }]


# ──────────────────────────────────────────────
# RENDER CHAT HISTORY
# ──────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="user-bubble">{msg["content"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="bot-bubble">', unsafe_allow_html=True)
        st.markdown(msg["content"])
        st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# PREFILL FROM SIDEBAR BUTTONS
# ──────────────────────────────────────────────
prefill = st.session_state.pop("prefill", None)

# ──────────────────────────────────────────────
# CHAT INPUT
# ──────────────────────────────────────────────
user_input = st.chat_input("Ask about a stock, trade setup, or portfolio...")
if prefill:
    user_input = prefill

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.markdown(
        f'<div class="user-bubble">{user_input}</div>',
        unsafe_allow_html=True,
    )

    # Thinking indicator
    thinking = st.empty()
    thinking.markdown(
        '<div class="thinking-bar">'
        '<div class="dot1"></div><div class="dot2"></div><div class="dot3"></div>'
        '&nbsp; Analyzing...</div>',
        unsafe_allow_html=True,
    )

    # Run agent
    try:
        response = run_agent(user_input)
    except Exception as e:
        response = f"**Error:** `{str(e)}`\n\nCheck the terminal for a full traceback."

    thinking.empty()

    # Show response
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.markdown('<div class="bot-bubble">', unsafe_allow_html=True)
    st.markdown(response)
    st.markdown('</div>', unsafe_allow_html=True)