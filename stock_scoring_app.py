import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import pandas_ta as ta
import json

# ==========================================
# 1. CONFIGURATION
# ==========================================
GEMINI_API_KEY = "AIzaSyDRQsXmH0RGWso0GPKQlBu_IMa5ZjDSNfw"
genai.configure(api_key=GEMINI_API_KEY)

# Use 'gemini-1.5-flash' - it is faster and more widely available for v1beta
model = genai.GenerativeModel('gemini-1.5-flash')

def get_technical_data(ticker):
    """Fetches 100% current day price and technicals using yfinance"""
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")
    if hist.empty:
        return None
    
    # Current Day Metrics
    current_price = hist['Close'].iloc[-1]
    ma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
    rsi = ta.rsi(hist['Close'], length=14).iloc[-1]
    vol = hist['Volume'].iloc[-1]
    avg_vol = stock.info.get('averageVolume', 1)
    
    return {
        "Price": round(current_price, 2),
        "RSI": round(rsi, 2),
        "MA200": round(ma200, 2),
        "Vol": vol,
        "AvgVol": avg_vol,
        "raw_info": stock.info # Pass to Gemini for deeper extraction
    }

def fetch_scoring_via_gemini(ticker, tech_data):
    """Calls Gemini to fetch metrics from web/info and calculate final score"""
    
    prompt = f"""
    Analyze the stock {ticker} using the following real-time technicals: {tech_data}.
    Based on your training and search capabilities, find the Industry PE Limit, 3-year ROI Average, 
    and verify the current PE, PB, PEG, ROE, Debt/Eq, Beta, DivYield, OpMargin, FCF, and EPS.
    
    APPLY THIS SCORING LOGIC (Points 1-10 per metric):
    1. VALUE (30% weight): P/E (<15=10 pts, else lower), P/B (<1=10 pts), PEG (<1=10 pts), PE < Industry PE.
    2. SAFETY (30% weight): ROE (>15=10), Debt/Eq (<100=10), Beta (<1=10), DivYield (>2%=10).
    3. MOMENTUM (20% weight): RSI (30-70=10), Price > MA200 (=10), Vol > AvgVol (=10).
    4. QUALITY (20% weight): OpMargin (>20%=10), FCF (Positive=10), EPS (Positive=10), ROI 3yr Avg (>12=10).

    Return ONLY a JSON object with this structure:
    {{
        "metrics": {{ "PE": 0, "PB": 0, "PEG": 0, "Ind_PE": 0, "ROE": 0, "DebtEq": 0, "Beta": 0, "DivYield": 0, "OpMargin": 0, "FCF": 0, "EPS": 0, "ROI3yr": 0 }},
        "cat_scores": {{ "Value": 0, "Safety": 0, "Momentum": 0, "Quality": 0 }},
        "final_score": 0,
        "signal": "BUY / SELL / HOLD"
    }}
    """
    
    response = model.generate_content(prompt)
    # Clean response in case AI adds markdown code blocks
    clean_json = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(clean_json)

# ==========================================
# 2. STREAMLIT UI
# ==========================================
st.set_page_config(page_title="Gemini Live Scorer", layout="wide")
st.title("📈 Gemini Stock Scoring Terminal")

ticker_input = st.text_input("Enter Stock Ticker (e.g., ITC.NS, RELIANCE.NS, TSLA):").upper()

if ticker_input:
    with st.spinner(f"Pulling Live Data for {ticker_input}..."):
        try:
            # Step 1: Get 100% current technicals
            tech = get_technical_data(ticker_input)
            
            if tech:
                # Step 2: Use Gemini for Metrics & Score calculation
                result = fetch_scoring_via_gemini(ticker_input, tech)
                
                # Step 3: Display Signal
                score = result['final_score']
                if score >= 7:
                    st.success(f"## FINAL SCORE: {score} - 🚀 {result['signal']}")
                elif score <= 5:
                    st.error(f"## FINAL SCORE: {score} - ⚠️ {result['signal']}")
                else:
                    st.warning(f"## FINAL SCORE: {score} - ⚖️ {result['signal']}")
                
                # Category Breakdown
                cols = st.columns(4)
                cols[0].metric("Value (30%)", f"{result['cat_scores']['Value']}/10")
                cols[1].metric("Safety (30%)", f"{result['cat_scores']['Safety']}/10")
                cols[2].metric("Momentum (20%)", f"{result['cat_scores']['Momentum']}/10")
                cols[3].metric("Quality (20%)", f"{result['cat_scores']['Quality']}/10")
                
                # Data Tables
                st.subheader("Data Audit (Current Day)")
                df_metrics = pd.DataFrame([result['metrics']]).T.rename(columns={0: "Value"})
                st.table(df_metrics)
                
                with st.expander("View Technicals (yfinance)"):
                    st.write(tech)
            else:
                st.error("Ticker not found. Please try again.")
                
        except Exception as e:
            st.error(f"Error: {e}")
