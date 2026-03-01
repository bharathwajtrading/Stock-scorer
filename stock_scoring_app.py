import streamlit as st
import google.generativeai as genai
import pandas as pd
import json

# ==========================================
# 1. API CONFIGURATION
# ==========================================
# REPLACEMENT: Use gemini-2.0-flash for stability
API_KEY = "AIzaSyBOn3zckFKolrvzN9qtoRyLDZjv6jtTlko" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# ==========================================
# 2. SCORING ENGINE (Reverted to Sheet 3 Logic)
# ==========================================
def calculate_scores(d):
    # Value (30%)
    pe_s = 10 if d['PE'] < 15 else (8 if d['PE'] < 30 else 5)
    pb_s = 10 if d['PB'] < 2 else (8 if d['PB'] < 3.5 else 1)
    val_score = (pe_s + pb_s) / 2

    # Safety (30%)
    roe_s = 10 if d['ROE'] > 20 else (8 if d['ROE'] > 15 else 5)
    debt_s = 10 if d['DebtEq'] < 0.1 else (5 if d['DebtEq'] < 0.8 else 1)
    safe_score = (roe_s + debt_s) / 2

    # Momentum (20%)
    rsi_s = 10 if 30 <= d['RSI'] <= 40 else (7 if d['RSI'] <= 50 else 2)
    mom_score = rsi_s # Simplified for UI demo

    # Quality (20%)
    qual_score = 10 if d['OpMargin'] > 25 else 5

    final = (val_score * 0.3) + (safe_score * 0.3) + (mom_score * 0.2) + (qual_score * 0.2)
    return {"V": val_score, "S": safe_score, "M": mom_score, "Q": qual_score, "Total": round(final, 2)}

# ==========================================
# 3. GUI DESIGN
# ==========================================
st.set_page_config(page_title="Stock Scorer Pro", layout="wide")

st.markdown("""
    <style>
    .verdict-box { padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 25px; color: white; font-weight: bold; }
    .buy { background-color: #27ae60; border: 2px solid #2ecc71; }
    .hold { background-color: #f39c12; border: 2px solid #f1c40f; }
    .sell { background-color: #c0392b; border: 2px solid #e74c3c; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Institutional Stock Analysis Terminal")
ticker = st.text_input("Search Stock Ticker (e.g., ITC.NS, RELIANCE.NS):", "").upper()

if ticker:
    with st.spinner("AI is scanning live market parameters..."):
        # SEARCH PROMPT
        prompt = f"""
        Search for LIVE data for {ticker}. Return ONLY JSON:
        {{ "Price": 0.0, "PE": 0.0, "PB": 0.0, "ROE": 0.0, "DebtEq": 0.0, "RSI": 0.0, "OpMargin": 0.0, "PEG": 0.0, "Beta": 0.0 }}
        """
        
        try:
            response = model.generate_content(prompt)
            data = json.loads(response.text.replace('```json', '').replace('```', '').strip())
            scores = calculate_scores(data)

            # --- DISPLAY SECTION ---
            
            # 1. FINAL SCORE (Colored)
            score = scores['Total']
            verdict_class = "buy" if score > 7 else ("hold" if score > 5 else "sell")
            verdict_text = "STRONG BUY" if score > 7 else ("NEUTRAL / HOLD" if score > 5 else "AVOID / SELL")
            
            st.markdown(f'<div class="verdict-box {verdict_class}"><h1>{verdict_text}</h1><h2>Final Score: {score} / 10</h2></div>', unsafe_allow_html=True)

            # 2. CATEGORY SCORES
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Value Score", f"{scores['V']}/10")
            c2.metric("Safety Score", f"{scores['S']}/10")
            c3.metric("Momentum Score", f"{scores['M']}/10")
            c4.metric("Quality Score", f"{scores['Q']}/10")

            st.divider()

            # 3. METRICS TABLE
            st.subheader("📋 Fundamental & Technical Parameters")
            metrics_df = pd.DataFrame([data]).T.rename(columns={0: "Current Value"})
            st.table(metrics_df)

        except Exception as e:
            st.error(f"Error: {e}. Try using the full ticker like 'ITC.NS'.")
