import streamlit as st
import pandas as pd

# Function to calculate scores

def calculate_scores(data):
    # Normalize metrics
    pe_score = 1 / data['P/E'] if data['P/E'] > 0 else 0
    roe_score = data['ROE'] / 100 if data['ROE'] > 0 else 0
    debt_equity_score = 1 - data['Debt/Equity'] if data['Debt/Equity'] < 1 else 0
    beta_score = 1 - data['Beta'] if data['Beta'] < 1 else 0
    rsi_score = 1 - (data['RSI'] / 100)
    operating_margin_score = data['Operating Margin'] / 100 if data['Operating Margin'] > 0 else 0
    fcf_score = data['FCF'] / 100 if data['FCF'] > 0 else 0
    eps_score = data['EPS'] / 10 if data['EPS'] > 0 else 0

    # Aggregate scores
    value_score = pe_score
    momentum_score = rsi_score
    safety_score = (debt_equity_score + beta_score) / 2
    quality_score = (roe_score + operating_margin_score + fcf_score + eps_score) / 4

    return {"Value": value_score, "Momentum": momentum_score, "Safety": safety_score, "Quality": quality_score}

# Streamlit UI

st.title('Stock Scoring Application')

# Input fields for stock metrics
st.subheader('Input Stock Metrics')
pe = st.number_input('P/E Ratio', min_value=0.0, format="%.2f")
roe = st.number_input('ROE (%)', min_value=0.0, format="%.2f")
debt_equity = st.number_input('Debt/Equity Ratio', min_value=0.0, format="%.2f")
beta = st.number_input('Beta', min_value=0.0, format="%.2f")
rsi = st.number_input('RSI', min_value=0.0, format="%.2f")
operating_margin = st.number_input('Operating Margin (%)', min_value=0.0, format="%.2f")
fcf = st.number_input('Free Cash Flow', min_value=0.0, format="%.2f")
eps = st.number_input('EPS', min_value=0.0, format="%.2f")

# Calculate and display scores when the button is pressed
if st.button('Calculate Scores'):
    metrics = {
        'P/E': pe,
        'ROE': roe,
        'Debt/Equity': debt_equity,
        'Beta': beta,
        'RSI': rsi,
        'Operating Margin': operating_margin,
        'FCF': fcf,
        'EPS': eps
    }
    scores = calculate_scores(metrics)
    st.subheader('Stock Scores')
    st.write(scores)