
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.set_page_config(page_title="Stock Quality Scorer 2026", layout="wide")

st.title("📈 Stock Scoring App (Target 2026)")
st.write("Enter an NSE/BSE ticker to get a real-time score based on your Quality, Value, and Momentum metrics.")

# 1. Input Ticker
ticker_input = st.text_input("Enter Ticker (e.g., ITC.NS, SBIN.NS, KALYANKJIL.NS)", "ITC.NS")

if ticker_input:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info
        hist = stock.history(period="1y")

        # --- DATA EXTRACTION ---
        price = info.get('currentPrice', 0)
        pe = info.get('trailingPE', 0)
        pb = info.get('priceToBook', 0)
        peg = info.get('pegRatio', 0)
        roe = info.get('returnOnEquity', 0) * 100
        debt_eq = info.get('debtToEquity', 0) / 100
        beta = info.get('beta', 0)
        div_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
        eps = info.get('trailingEps', 0)
        op_margin = info.get('operatingMargins', 0) * 100
        avg_vol = info.get('averageVolume', 0)
        
        # Technicals
        rsi = ta.rsi(hist['Close'], length=14).iloc[-1]
        sma200 = hist['Close'].rolling(window=200).mean().iloc[-1]

        # --- SCORING LOGIC (0-10 Scale) ---
        score = 0
        
        # Value (Max 3 pts)
        if pe < 20: score += 1.5
        if peg < 1.2: score += 1.5
        
        # Quality (Max 3 pts)
        if roe > 20: score += 1.5
        if op_margin > 25: score += 1.5
        
        # Safety (Max 2 pts)
        if beta < 1: score += 1
        if debt_eq < 0.5: score += 1
        
        # Momentum (Max 2 pts)
        if 40 < rsi < 65: score += 1
        if price > sma200: score += 1

        # --- DISPLAY RESULTS ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Current Price", f"₹{price}")
            st.subheader(f"Final Score: {round(score, 1)} / 10")
            
            if score >= 7:
                st.success("🔥 ACTION: BUY (Strong Fundamentals/Momentum)")
            elif score <= 5:
                st.error("⚠️ ACTION: SELL (Overvalued/Weak Quality)")
            else:
                st.warning("⚖️ ACTION: HOLD (Neutral Zone)")

        with col2:
            st.write("**Key Metrics Found:**")
            data = {
                "Metric": ["P/E Ratio", "PEG Ratio", "ROE %", "Debt/Equity", "Beta", "RSI (14D)", "Div Yield %"],
                "Value": [pe, peg, f"{round(roe,2)}%", debt_eq, beta, round(rsi,2), f"{round(div_yield,2)}%"]
            }
            st.table(pd.DataFrame(data))

    except Exception as e:
        st.error(f"Error fetching data: {e}. Please ensure the ticker suffix is correct (e.g., .NS for NSE).")

st.divider()
st.caption("Data provided by Yahoo Finance API. Scoring weights: Value (30%), Quality (30%), Safety (20%), Momentum (20%).")
