import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import pandas_ta as ta

# 1. API CONFIGURATION
GEMINI_API_KEY = "AIzaSyDRQsXmH0RGWso0GPKQlBu_IMa5ZjDSNfw"
genai.configure(api_key=GEMINI_API_KEY)
# Using 'flash' for speed and stability
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. DATA FETCHING (Ensures 100% Current Day Data)
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    # Fetch 1 year data for technicals
    hist = stock.history(period="1y")
    if hist.empty: return None
    
    info = stock.info
    curr_price = hist['Close'].iloc[-1]
    
    # Technical Indicators (Current Day)
    ma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
    rsi = ta.rsi(hist['Close'], length=14).iloc[-1]
    
    # Basic Metrics
    data = {
        'Price': round(curr_price, 2),
        'PE': info.get('trailingPE', 0),
        'PB': info.get('priceToBook', 0),
        'PEG': info.get('pegRatio', 0),
        'ROE': (info.get('returnOnEquity', 0) or 0) * 100,
        'DebtEq': info.get('debtToEquity', 0),
        'Beta': info.get('beta', 0),
        'DivYield': (info.get('dividendYield', 0) or 0) * 100,
        'RSI': round(rsi, 2),
        'MA200': round(ma200, 2),
        'Vol': hist['Volume'].iloc[-1],
        'AvgVol': info.get('averageVolume', 1),
        'OpMargin': (info.get('operatingMargins', 0) or 0) * 100,
        'FCF': info.get('freeCashflow', 0),
        'EPS': info.get('trailingEps', 0)
    }
    return data

# 3. GEMINI RESEARCH (For missing Sheet metrics)
def get_industry_metrics(ticker):
    prompt = f"Search for the current Industry PE limit and 3-year average ROI for {ticker}. Return ONLY numbers separated by a comma. Example: 25.5, 18.2"
    try:
        response = model.generate_content(prompt)
        vals = response.text.strip().split(',')
        return float(vals[0]), float(vals[1])
    except:
        return 20.0, 15.0 # Fallbacks if AI search fails

# 4. SCORING LOGIC (Matches Sheet 3)
def calculate_scores(d, ind_pe, roi3):
    # VALUE (30%)
    v1 = 10 if d['PE'] < 15 else (8 if d['PE'] < 25 else 5)
    v2 = 10 if d['PB'] < 2 else (5 if d['PB'] < 4 else 1)
    v3 = 10 if d['PEG'] < 1 else 5
    v_score = (v1 + v2 + v3) / 3
    
    # SAFETY (30%)
    s1 = 10 if d['ROE'] > 20 else (5 if d['ROE'] > 12 else 2)
    s2 = 10 if d['DebtEq'] < 50 else (5 if d['DebtEq'] < 100 else 1)
    s3 = 10 if d['Beta'] < 1 else 5
    s4 = 10 if d['DivYield'] > 3 else (5 if d['DivYield'] > 1 else 0)
    s_score = (s1 + s2 + s3 + s4) / 4
    
    # MOMENTUM (20%)
    m1 = 10 if 30 < d['RSI'] < 45 else (7 if d['RSI'] < 60 else 3)
    m2 = 10 if d['Price'] > d['MA200'] else 1
    m3 = 10 if d['Vol'] > d['AvgVol'] else 5
    m_score = (m1 + m2 + m3) / 3
    
    # QUALITY (20%)
    q1 = 10 if d['OpMargin'] > 25 else (5 if d['OpMargin'] > 15 else 2)
    q2 = 10 if d['FCF'] > 0 else 0
    q3 = 10 if d['EPS'] > 0 else 0
    q_score = (q1 + q2 + q3) / 3
    
    final = (v_score * 0.3) + (s_score * 0.3) + (m_score * 0.2) + (q_score * 0.2)
    return round(v_score, 2), round(s_score, 2), round(m_score, 2), round(q_score, 2), round(final, 2)

# 5. STREAMLIT INTERFACE
st.title("🚀 Real-Time Stock Scoring Terminal")
ticker = st.text_input("Enter Ticker (e.g. ITC.NS):").upper()

if ticker:
    with st.spinner("Fetching Live Market Data..."):
        d = get_stock_data(ticker)
        if d:
            ind_pe, roi3 = get_industry_metrics(ticker)
            v, s, m, q, final = calculate_scores(d, ind_pe, roi3)
            
            # Show Results
            if final >= 7: st.success(f"### Score: {final} / 10 - BUY 🚀")
            elif final <= 5: st.error(f"### Score: {final} / 10 - SELL ⚠️")
            else: st.warning(f"### Score: {final} / 10 - HOLD ⚖️")
            
            cols = st.columns(4)
            cols[0].metric("Value", f"{v}/10")
            cols[1].metric("Safety", f"{s}/10")
            cols[2].metric("Momentum", f"{m}/10")
            cols[3].metric("Quality", f"{q}/10")
            
            st.table(pd.DataFrame([d]).T.rename(columns={0: "Live Data Point"}))
        else:
            st.error("Invalid Ticker. Please use .NS for Indian stocks.")
