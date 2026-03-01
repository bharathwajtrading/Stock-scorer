import streamlit as st
import requests
import pandas as pd

def fetch_stock_data(ticker):
    # Sample API call, replace with actual API URL
    url = f'https://api.example.com/stock/{ticker}'
    response = requests.get(url)
    return response.json()

def calculate_scores(metrics):
    # calculations for Value, Momentum, Safety, and Quality
    value_score = (metrics['P/E'] < 15) + (metrics['P/B'] < 1) + (metrics['PEG'] < 1)
    momentum_score = (metrics['EPS Growth'] > 0) + (metrics['FCF Growth'] > 0)
    safety_score = (metrics['Debt/Equity'] < 1) + (metrics['Beta'] < 1)
    quality_score = (metrics['ROE'] > 15) + (metrics['Dividend Yield'] > 2) + (metrics['Operating Margin'] > 20)
    return value_score, momentum_score, safety_score, quality_score

st.title('Stock Scoring App')

ticker = st.text_input('Enter stock ticker symbol:')

if st.button('Fetch Metrics'):
    if ticker:
        metrics = fetch_stock_data(ticker)
        value_score, momentum_score, safety_score, quality_score = calculate_scores(metrics)
        st.write(f'Value Score: {value_score}')
        st.write(f'Momentum Score: {momentum_score}')
        st.write(f'Safety Score: {safety_score}')
        st.write(f'Quality Score: {quality_score}')
    else:
        st.error('Please enter a ticker symbol.')