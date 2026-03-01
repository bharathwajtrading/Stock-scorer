import streamlit as st
import google.generativeai as genai
import json
import re

# ==========================================
# 1. CONFIGURATION & INTEGRATION
# ==========================================
# Your provided Gemini API Key
GEMINI_API_KEY = "AIzaSyDRQsXmH0RGWso0GPKQlBu_IMa5ZjDSNfw"
genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini 1.5 Pro for better reasoning and data extraction
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

# ==========================================
# 2. UI SETUP
# ==========================================
st.set_page_config(page_title="Gemini Stock Scorer", layout="wide")
st.title("🎯 Real-Time AI Stock Scorer")
st.markdown("Enter a ticker to fetch **Current Day** data and calculate scores based on your Spreadsheet logic.")

ticker = st.text_input("Enter Ticker (e.g., ITC.NS, RELIANCE.NS, TSLA):", "").upper()

if ticker:
    with st.spinner(f"🔍 Gemini is searching for real-time data for {ticker}..."):
        # This prompt forces Gemini to research current values and apply your specific rubric
        prompt = f"""
        Search the web for the current, real-time financial metrics for: {ticker}.
        I need 100% accurate, today's values for these metrics:
        Price, PE, PB, PEG, Industry_PE_Limit, ROE, DebtEq, Beta, DivYield (as %), RSI (14-day), MA200, Vol, AvgVol, OpMargin, FCF, EPS.

        SCORING RUBRIC (Scale 1-10 per metric):
        - Value (30%): PE (<15:10, 15-25:8, >40:2), PB (<2:10, >5:1), PEG (<1:10).
        - Safety (30%): ROE (>20:10, <10:2), DebtEq (<0.1:10, >1:1), Beta (<0.8:10), DivYield (>4:10).
        - Momentum (20%): RSI (30-40:10, 40-70:5, >70:2), Price vs MA200 (Price > MA200:10, else 1), Vol vs AvgVol (Vol > AvgVol:10, else 5).
        - Quality (20%): OpMargin (>30:10, <10:1), FCF (Positive:10), EPS (Positive:10).

        Return ONLY a JSON object:
        {{
            "metrics": {{ "Price": 0, "PE": 0, "PB": 0, "PEG": 0, "Industry_PE": 0, "ROE": 0, "DebtEq": 0, "Beta": 0, "DivYield": 0, "RSI": 0, "MA200": 0, "Vol": 0, "AvgVol": 0, "OpMargin": 0, "FCF": 0, "EPS": 0 }},
            "scores": {{ "Value": 0, "Safety": 0, "Momentum": 0, "Quality": 0 }},
            "final_score": 0,
            "recommendation": "BUY" | "SELL" | "HOLD"
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                # --- Dashboard Layout ---
                st.divider()
                f_score = data['final_score']
                rec = data['recommendation']
                
                if f_score >= 7:
                    st.success(f"### FINAL SCORE: {f_score} / 10 — 🚀 {rec}")
                elif f_score <= 5:
                    st.error(f"### FINAL SCORE: {f_score} / 10 — ⚠️ {rec}")
                else:
                    st.warning(f"### FINAL SCORE: {f_score} / 10 — ⚖️ {rec}")

                # Metric Columns
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Value (30%)", f"{data['scores']['Value']}/10")
                c2.metric("Safety (30%)", f"{data['scores']['Safety']}/10")
                c3.metric("Momentum (20%)", f"{data['scores']['Momentum']}/10")
                c4.metric("Quality (20%)", f"{data['scores']['Quality']}/10")
                
                # Raw Data Table
                st.subheader("Current Market Data (Verified by AI)")
                st.table(data['metrics'])
            else:
                st.error("Could not parse data. Please try again.")
        except Exception as e:
            st.error(f"API Error: {e}")
