import streamlit as st
import google.generativeai as genai
import pandas as pd
import json

# ==========================================
# 1. API CONFIGURATION
# ==========================================
# Secure your key in Streamlit Secrets in production
GEMINI_API_KEY = "AIzaSyDRQsXmH0RGWso0GPKQlBu_IMa5ZjDSNfw"
genai.configure(api_key=GEMINI_API_KEY)

# Using Flash for speed and search capability
model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 2. SCORING ENGINE (Sheet 3 Logic)
# ==========================================
def calculate_scores(d):
    # Value Scores (30% weight)
    pe_s = 10 if d['PE'] < 15 else (8 if d['PE'] < 30 else 5)
    pb_s = 10 if d['PB'] < 2 else (8 if d['PB'] < 3.5 else (5 if d['PB'] < 5 else 1))
    peg_s = 10 if d['PEG'] < 1 else (8 if d['PEG'] < 1.2 else 5)
    val_score = (pe_s + pb_s + peg_s) / 3

    # Safety Scores (30% weight)
    roe_s = 10 if d['ROE'] > 20 else (8 if d['ROE'] > 15 else (5 if d['ROE'] > 10 else 2))
    debt_s = 10 if d['DebtEq'] < 0.1 else (5 if d['DebtEq'] < 0.8 else 1)
    beta_s = 10 if d['Beta'] < 1 else 5
    div_s = 10 if d['DivYield'] > 3 else (5 if d['DivYield'] > 1 else 2)
    safe_score = (roe_s + debt_s + beta_s + div_s) / 4

    # Momentum Scores (20% weight)
    rsi_s = 10 if 30 <= d['RSI'] <= 40 else (7 if d['RSI'] <= 50 else (5 if d['RSI'] <= 70 else 2))
    dma_s = 10 if d['Price'] > d['MA200'] else 1
    mom_score = (rsi_s + dma_s) / 2

    # Quality Scores (20% weight)
    mar_s = 10 if d['OpMargin'] > 25 else (5 if d['OpMargin'] > 15 else 2)
    fcf_s = 10 if d['FCF'] == "Positive" else 1
    eps_s = 10 if d['EPS'] > 0 else 1
    qual_score = (mar_s + fcf_s + eps_s) / 3

    final = (val_score * 0.3) + (safe_score * 0.3) + (mom_score * 0.2) + (qual_score * 0.2)
    
    return {
        "Value": round(val_score, 2),
        "Safety": round(safe_score, 2),
        "Momentum": round(mom_score, 2),
        "Quality": round(qual_score, 2),
        "Final": round(final, 2)
    }

# ==========================================
# 3. GUI & APP LOGIC
# ==========================================
st.set_page_config(page_title="Pro Stock Scorer", layout="wide")

# Custom CSS for different colors
st.markdown("""
    <style>
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; }
    .final-buy { background-color: #d4edda; color: #155724; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #c3e6cb; }
    .final-hold { background-color: #fff3cd; color: #856404; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #ffeeba; }
    .final-sell { background-color: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #f5c6cb; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Institutional Stock Scoring Terminal")
st.write("Fetching real-time data via Google Search AI...")

ticker = st.text_input("Enter Ticker (e.g. ITC, RELIANCE, TSLA):", "").upper()

if ticker:
    with st.spinner(f"AI is searching Live Market Data for {ticker}..."):
        # The AI prompt specifically forces searching for current Day values
        prompt = f"""
        Search for the CURRENT DAY (March 2026) financial data for {ticker}. 
        Be extremely accurate with the P/E ratio.
        Return ONLY a JSON object with these keys: 
        "Price", "PE", "PB", "PEG", "ROE", "DebtEq", "Beta", "DivYield", "RSI", "MA200", "OpMargin", "FCF", "EPS"
        Note: For FCF, return "Positive" or "Negative". For percentages like ROE, return as number (e.g. 28.5).
        """
        
        try:
            response = model.generate_content(prompt)
            # Cleanup AI response to get pure JSON
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(raw_text)
            
            # Calculate Scores
            scores = calculate_scores(data)

            # --- DISPLAY SECTION ---
            
            # 1. Final Score with Color Logic
            f = scores['Final']
            if f >= 7.5:
                st.markdown(f'<div class="final-buy"><h1>FINAL SCORE: {f} / 10 (STRONG BUY 🚀)</h1></div>', unsafe_allow_html=True)
            elif f >= 5.5:
                st.markdown(f'<div class="final-hold"><h1>FINAL SCORE: {f} / 10 (HOLD ⚖️)</h1></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="final-sell"><h1>FINAL SCORE: {f} / 10 (SELL ⚠️)</h1></div>', unsafe_allow_html=True)

            st.divider()

            # 2. Category Wise Scores
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Value (30%)", f"{scores['Value']}/10")
            col2.metric("Safety (30%)", f"{scores['Safety']}/10")
            col3.metric("Momentum (20%)", f"{scores['Momentum']}/10")
            col4.metric("Quality (20%)", f"{scores['Quality']}/10")

            st.divider()

            # 3. Metrics Table
            st.subheader("📋 Detailed Market Parameters (Fetched via AI)")
            df = pd.DataFrame([data]).T.rename(columns={0: "Live Value"})
            st.table(df)

        except Exception as e:
            st.error(f"Error fetching data for {ticker}. Please ensure the ticker is correct. Error: {e}")
