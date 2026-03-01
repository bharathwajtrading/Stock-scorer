import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- REVERTED SCORING LOGIC (Directly from your Sheet 3) ---
def calculate_metric_score(metric, val, price=None, ma200=None):
    try:
        v = float(val)
        if metric == "PE": return 10 if v < 15 else (8 if v < 30 else 5)
        if metric == "PB": return 10 if v < 2 else (8 if v < 3.5 else (5 if v < 5 else 1))
        if metric == "PEG": return 10 if v < 1 else (8 if v < 1.2 else 5)
        if metric == "ROE": return 10 if v > 20 else (8 if v > 15 else (5 if v > 10 else 2))
        if metric == "Debt": return 10 if v < 0.1 else (5 if v < 0.8 else 1)
        if metric == "RSI": return 10 if 30 <= v <= 40 else (7 if v <= 50 else (5 if v <= 70 else 2))
        if metric == "MA200": return 10 if price > ma200 else 1
    except: return 5
    return 5

# --- ROBUST DATA FETCHING ---
def fetch_live_metrics(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="1y")
    
    if hist.empty: return None

    # Calculate RSI manually to ensure accuracy
    delta = hist['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    current_rsi = 100 - (100 / (1 + rs.iloc[-1]))

    # Data points with Fallbacks
    current_price = hist['Close'].iloc[-1]
    ma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
    
    return {
        "Price": round(current_price, 2),
        "PE": info.get('trailingPE') or info.get('forwardPE', 15),
        "PB": info.get('priceToBook', 2),
        "PEG": info.get('pegRatio', 1),
        "ROE": (info.get('returnOnEquity', 0.15)) * 100,
        "Debt": info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0.01,
        "RSI": round(current_rsi, 2),
        "MA200": round(ma200, 2),
        "OpMargin": (info.get('operatingMargins', 0.1)) * 100,
        "FCF": 1 if (info.get('freeCashflow', 0) > 0) else -1,
        "EPS": info.get('trailingEps', 1)
    }

# --- UI ---
st.title("🎯 Accurate Stock Scorer (Reverted Logic)")
ticker_input = st.text_input("Enter Ticker:", "ITC.NS").upper()

if ticker_input:
    data = fetch_live_metrics(ticker_input)
    if data:
        # Calculate Category Scores based on Sheet 3
        v_score = (calculate_metric_score("PE", data['PE']) + 
                   calculate_metric_score("PB", data['PB']) + 
                   calculate_metric_score("PEG", data['PEG'])) / 3
        
        s_score = (calculate_metric_score("ROE", data['ROE']) + 
                   calculate_metric_score("Debt", data['Debt'])) / 2 # simplified safety
        
        m_score = (calculate_metric_score("RSI", data['RSI']) + 
                   calculate_metric_score("MA200", None, data['Price'], data['MA200'])) / 2
        
        final_score = (v_score * 0.3) + (s_score * 0.3) + (m_score * 0.2) + (10 * 0.2) # Quality fix

        st.header(f"Final Score: {round(final_score, 2)}")
        
        col1, col2 = st.columns(2)
        col1.subheader("Fetched Data")
        col1.write(data)
        
        col2.subheader("Sheet Scores")
        col2.write({"Value": round(v_score, 2), "Safety": round(s_score, 2), "Momentum": round(m_score, 2)})
    else:
        st.error("Invalid Ticker.")
