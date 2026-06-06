"""
NYSE Breakout Stock Screener - Mobile App
Streamlit-based responsive web app that works on phones, tablets, and desktop
Deploy for free on Streamlit Cloud: https://streamlit.io/cloud
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from streamlit_option_menu import option_menu
import warnings
warnings.filterwarnings('ignore')

# Set page configuration for mobile
st.set_page_config(
    page_title="NYSE Breakout Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile optimization
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
    }
    
    .main {
        padding: 0.5rem;
    }
    
    .stMetric {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #667eea;
    }
    
    h1 {
        color: #667eea;
        font-size: 1.8rem;
        margin-bottom: 1rem;
    }
    
    h2 {
        color: #764ba2;
        font-size: 1.3rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .data-table {
        font-size: 0.9rem;
    }
    
    @media (max-width: 768px) {
        .main {
            padding: 0.3rem;
        }
        h1 {
            font-size: 1.5rem;
        }
        h2 {
            font-size: 1.1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CORE SCREENING ENGINE
# ============================================================================

class MobileBreakoutScreener:
    """Optimized breakout screener for mobile"""
    
    def __init__(self):
        self.stocks = [
            'AAPL', 'MSFT', 'NVDA', 'GOOG', 'META', 'TSLA', 'NFLX', 'AMD',
            'AVGO', 'INTC', 'QCOM', 'ADBE', 'CRM', 'SNPS', 'CDNS', 'AMAT',
            'JNJ', 'PG', 'WMT', 'MCD', 'V', 'MA', 'JPM', 'BAC', 'GS', 'MS'
        ]
    
    def get_stock_data(self, symbol, period='1y'):
        """Fetch stock data"""
        try:
            data = yf.download(symbol, period=period, progress=False)
            return data if len(data) > 50 else None
        except:
            return None
    
    def calculate_indicators(self, data):
        """Calculate technical indicators"""
        if data is None or len(data) < 50:
            return None
        
        df = data.copy()
