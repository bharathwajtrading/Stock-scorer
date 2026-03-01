import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- SCORING ENGINE (Matches your Colored Columns) ---
def get_score(metric, value, price=None, dma=None):
    try:
        val = float(value)
        if metric == "PE": return 10 if val < 15 else (8 if val < 25 else 5)
        if metric == "PB": return 10 if val < 2 else (5 if val < 4 else 1)
        if metric == "PEG": return 10 if val < 1 else 5
        if metric == "ROE": return 10 if val > 20 else (8 if val > 15 else 5)
        if metric == "DebtEq": return 10 if val < 0.5 else (5 if val < 1 else 1)
        if metric == "Beta": return 10 if val < 1 else 5
        if metric == "DivYield": return 10 if val > 3 else (5 if val > 1 else 2)
        if metric == "RSI":
            if 30 <= val <= 40: return 10 
            if 40 < val <= 60: return 7
            return 5
        if metric == "200DMA": return 10 if price > dma else 1
        if metric == "OpMargin": return 10 if val > 25 else 5
        if metric == "FCF": return 10 if val > 0 else 1
        if metric == "EPS": return 10 if val > 0 else 1
    except: return 5
    return 5

# --- APP INTERFACE ---
st.set_page_config(page_title="Stock Scorer Pro", layout="wide")
st.title("📈 Live Market Scorer (Sheet 3 Logic)")

ticker = st.text_input("Enter Ticker (e.g., ITC.NS, RELIANCE.NS):").upper()

if ticker:
    with st.spinner("Fetching Current Day Data..."):
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        if not hist.empty:
            info = stock.info
            price = hist['Close'].iloc[-1]
            dma = hist['Close'].rolling(window=200).mean().iloc[-1]
            rsi = ta.rsi(hist['Close'], length=14).iloc[-1]
            
            # --- Gather Raw Data ---
            raw = {
                "PE": info.get('trailingPE', 0),
                "PB": info.get('priceToBook', 0),
                "PEG": info.get('pegRatio', 0),
                "ROE": (info.get('returnOnEquity', 0) or 0) * 100,
                "DebtEq": info.get('debtToEquity', 0),
                "Beta": info.get('beta', 0),
                "DivYield": (info.get('dividendYield', 0) or 0) * 100,
                "RSI": rsi,
                "OpMargin": (info.get('operatingMargins', 0) or 0) * 100,
                "FCF": info.get('freeCashflow', 1),
                "EPS": info.get('trailingEps', 1)
            }

            # --- Generate Scores (The Coloured Columns) ---
            scores = {
                "Value": (get_score("PE", raw["PE"]) + get_score("PB", raw["PB"]) + get_score("PEG", raw["PEG"])) / 3,
                "Safety": (get_score("ROE", raw["ROE"]) + get_score("DebtEq", raw["DebtEq"]) + get_score("Beta", raw["Beta"]) + get_score("DivYield", raw["DivYield"])) / 4,
                "Momentum": (get_score("RSI", raw["RSI"]) + get_score("200DMA", None, price, dma)) / 2,
                "Quality": (get_score("OpMargin", raw["OpMargin"]) + get_score("FCF", raw["FCF"]) + get_score("EPS", raw["EPS"])) / 3
            }
            
            final_score = (scores["Value"] * 0.3) + (scores["Safety"] * 0.3) + (scores["Momentum"] * 0.2) + (scores["Quality"] * 0.2)

            # --- Display ---
            st.metric("FINAL SCORE", f"{round(final_score, 2)} / 10", delta="Live Update")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 Category Scores (1-10)")
                st.write(scores)
            with col2:
                st.subheader("📝 Raw Data (Fetched Today)")
                st.write({k: round(v, 2) for k, v in raw.items()})
                st.write(f"Current Price: {round(price, 2)} | 200DMA: {round(dma, 2)}")

        else:
            st.error("Ticker not found. Try adding .NS for NSE stocks.")
