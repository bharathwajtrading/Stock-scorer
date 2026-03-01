import streamlit as st
import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        if hist.empty: return None

        # Data extraction strictly following Sheet 3 categories
        return {
            # Value Category
            'PE': info.get('trailingPE', 0),
            'PB': info.get('priceToBook', 0),
            'PEG': info.get('pegRatio', 0),
            'Industry_PE_Limit': info.get('forwardPE', 0), # Using forward PE as proxy for limit
            
            # Safety Category
            'ROE': (info.get('returnOnEquity', 0) or 0) * 100,
            'DebtEq': info.get('debtToEquity', 0),
            'Beta': info.get('beta', 1),
            'DivYield': (info.get('dividendYield', 0) or 0) * 100,
            
            # Momentum Category
            'Price': info.get('currentPrice', 0),
            'RSI': calculate_rsi(hist),
            'MA200': hist['Close'].rolling(window=200).mean().iloc[-1],
            'Vol': info.get('volume', 0),
            'AvgVol': info.get('averageVolume', 1),
            
            # Quality Category
            'OpMargin': (info.get('operatingMargins', 0) or 0) * 100,
            'FCF': info.get('freeCashflow', 0),
            'EPS': info.get('trailingEps', 0),
            'ROI_3yr_Avg': (info.get('returnOnAssets', 0) or 0) * 100 # Proxy for ROI average
        }
    except Exception as e:
        st.error(f"Error fetching {ticker}: {e}")
        return None

def calculate_rsi(hist):
    delta = hist['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs.iloc[-1]))

def calculate_category_scores(d):
    # Formulas and conditions based on Sheet 3
    
    # 1. VALUE (Weight: 30%)
    v_results = [
        10 if 0 < d['PE'] < 15 else 0,
        10 if 0 < d['PB'] < 1 else 0,
        10 if 0 < d['PEG'] < 1 else 0,
        10 if d['PE'] < d['Industry_PE_Limit'] else 0  # Additional condition
    ]
    v_score = sum(v_results) / len(v_results)

    # 2. SAFETY (Weight: 30%)
    s_results = [
        10 if d['ROE'] > 15 else 0,
        10 if d['DebtEq'] < 100 else 0,
        10 if d['Beta'] < 1 else 0,
        10 if d['DivYield'] > 2 else 0
    ]
    s_score = sum(s_results) / len(s_results)

    # 3. MOMENTUM (Weight: 20%)
    m_results = [
        10 if 30 < d['RSI'] < 70 else 0,
        10 if d['Price'] > d['MA200'] else 0,
        10 if d['Vol'] > d['AvgVol'] else 0
    ]
    m_score = sum(m_results) / len(m_results)

    # 4. QUALITY (Weight: 20%)
    q_results = [
        10 if d['OpMargin'] > 20 else 0,
        10 if d['FCF'] > 0 else 0,
        10 if d['EPS'] > 0 else 0,
        10 if d['ROI_3yr_Avg'] > 12 else 0  # Additional condition
    ]
    q_score = sum(q_results) / len(q_results)

    # Weighted Total Score
    total = (v_score * 0.30) + (s_score * 0.30) + (m_score * 0.20) + (q_score * 0.20)
    
    return round(v_score, 2), round(s_score, 2), round(m_score, 2), round(q_score, 2), round(total, 2)

# --- Streamlit Interface ---
st.set_page_config(page_title="Sheet 3 Stock Analyzer", layout="wide")
st.title("📊 Financial Scoring Model (Sheet 3 Logic)")

ticker = st.text_input("Enter Ticker Symbol:", value="AAPL").upper()

if ticker:
    with st.spinner(f"Analyzing {ticker}..."):
        data = fetch_stock_data(ticker)
        
    if data:
        v, s, m, q, final = calculate_category_scores(data)
        
        # Display Final Verdict
        if final > 7:
            st.success(f"### Score: {final} - 🚀 BUY SIGNAL")
        elif final < 5:
            st.error(f"### Score: {final} - ⚠️ SELL SIGNAL")
        else:
            st.warning(f"### Score: {final} - ⚖️ HOLD / WATCH")

        # Visual Breakdown
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Value (30%)", f"{v}/10")
        col2.metric("Safety (30%)", f"{s}/10")
        col3.metric("Momentum (20%)", f"{m}/10")
        col4.metric("Quality (20%)", f"{q}/10")

        # Detailed Data View
        with st.expander("View Metric Details"):
            st.table(pd.DataFrame([data]).T.rename(columns={0: 'Current Value'}))
