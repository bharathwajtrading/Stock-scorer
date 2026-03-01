
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.set_page_config(page_title="Stock Quality Scorer 2026", layout="wide")

st.title("📈 Stock Scoring App (Reliable Data Version)")
st.write("More stable data fetch using fast_info + fallback fundamentals.")

def safe_get(data, key, default=0):
    return data[key] if key in data and data[key] is not None else default

ticker = st.text_input("Enter Ticker (e.g., ITC.NS, SBIN.NS)", "ITC.NS")

if ticker:
    try:
        stock = yf.Ticker(ticker)

        fast = stock.fast_info
        hist = stock.history(period="1y")
        close = hist["Close"]

        price = fast.get("last_price", 0)
        sma200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else 0
        rsi = ta.rsi(close, length=14).iloc[-1]

        info = stock.get_info()

        pe = safe_get(info, "trailingPE", 0)
        pb = safe_get(info, "priceToBook", 0)
        peg = safe_get(info, "pegRatio", 0)
        roe = safe_get(info, "returnOnEquity", 0) * 100
        op_margin = safe_get(info, "operatingMargins", 0) * 100
        debt_eq = safe_get(info, "debtToEquity", 0) / 100
        beta = safe_get(info, "beta", 0)
        div_yield = safe_get(info, "dividendYield", 0) * 100

        score = 0

        if pe and pe < 20: score += 1.5
        if peg and peg < 1.2: score += 1.5
        if roe and roe > 20: score += 1.5
        if op_margin and op_margin > 25: score += 1.5
        if beta and beta < 1: score += 1
        if debt_eq and debt_eq < 0.5: score += 1
        if 40 < rsi < 65: score += 1
        if sma200 and price > sma200: score += 1

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Current Price", f"₹{price:,.2f}")
            st.subheader(f"Final Score: {round(score, 1)} / 10")

            if score >= 7:
                st.success("🔥 ACTION: BUY")
            elif score <= 5:
                st.error("⚠️ ACTION: SELL")
            else:
                st.warning("⚖️ ACTION: HOLD")

        with col2:
            st.write("### Key Metrics")
            df = pd.DataFrame({
                "Metric": ["P/E", "PEG", "ROE %", "Debt/Equity", "Beta", "RSI", "Dividend Yield %"],
                "Value": [pe, peg, round(roe, 2), debt_eq, beta, round(rsi, 2), round(div_yield, 2)]
            })
            st.table(df)

        st.divider()
        st.caption("Data rebuilt using fast_info + fallback fundamentals for stability.")

    except Exception as e:
        st.error(f"Error fetching data: {e}")
