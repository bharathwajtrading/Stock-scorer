
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.set_page_config(page_title="Stock Scorer Pro", layout="wide")

st.title("📈 Pro Stock Scorer (Full Metrics)")

ticker_input = st.text_input("Enter Ticker (e.g., ITC.NS, KALYANKJIL.NS)", "ITC.NS")

if ticker_input:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info
        hist = stock.history(period="1y")

        # --- REFINED DATA EXTRACTION ---
        price = info.get('currentPrice', info.get('navPrice', 0))
        pe = info.get('trailingPE', 0)
        # Fix ROE: handle None and decimals
        roe_raw = info.get('returnOnEquity', 0)
        roe = (roe_raw * 100) if roe_raw is not None else 0
        
        peg = info.get('pegRatio', 0) if info.get('pegRatio') is not None else 0
        debt_eq = info.get('debtToEquity', 0)
        beta = info.get('beta', 0)
        
        # Fix Div Yield: standardizing decimal
        div_raw = info.get('dividendYield', 0)
        div_yield = (div_raw * 100) if div_raw is not None else 0
        
        op_margin = (info.get('operatingMargins', 0) or 0) * 100
        eps = info.get('trailingEps', 0)
        avg_vol = info.get('averageVolume', 0)

        # Technicals
        rsi = ta.rsi(hist['Close'], length=14).iloc[-1] if len(hist) > 14 else 0
        sma200 = hist['Close'].rolling(window=200).mean().iloc[-1]

        # --- SCORING ---
        score = 0
        if 0 < pe < 20: score += 2
        if roe > 15: score += 2
        if 0 < peg < 1.5: score += 2
        if beta < 1: score += 2
        if price > sma200: score += 2

        # --- FULL DISPLAY TABLE ---
        st.subheader(f"Final Score: {round(score, 1)} / 10")
        
        full_data = {
            "Metric": ["Current Price", "P/E Ratio", "PEG Ratio", "ROE %", "Debt/Equity", "Beta", "Div Yield %", "Op. Margin %", "EPS", "RSI (14D)", "Avg Volume"],
            "Value": [f"₹{price}", round(pe, 2), round(peg, 2), f"{round(roe, 2)}%", round(debt_eq, 2), round(beta, 2), f"{round(div_yield, 2)}%", f"{round(op_margin, 2)}%", round(eps, 2), round(rsi, 2), f"{avg_vol:,}"]
        }
        st.table(pd.DataFrame(full_data))

    except Exception as e:
        st.error(f"Error: {e}")
