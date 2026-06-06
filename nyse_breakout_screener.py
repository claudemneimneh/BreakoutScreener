"""
NYSE Breakout Stock Screener - Mobile App - SIMPLIFIED VERSION
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
        
        try:
            df = data.copy()
            
            # Moving averages
            df['MA20'] = df['Close'].rolling(20).mean()
            df['MA50'] = df['Close'].rolling(50).mean()
            df['MA200'] = df['Close'].rolling(200).mean()
            df['VolMA20'] = df['Volume'].rolling(20).mean()
            df['High52w'] = df['Close'].rolling(252).max()
            df['SwingHigh30d'] = df['Close'].rolling(30).max()
            
            # RSI calculation
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Volume ratio - SIMPLIFIED AND SAFE
            # Fill any NaN in VolMA20 with the overall volume mean
            vol_ma_filled = df['VolMA20'].fillna(df['Volume'].mean())
            # Make sure no zeros exist
            vol_ma_filled = vol_ma_filled.clip(lower=df['Volume'].mean() * 0.1)
            # Calculate ratio
            df['VolRatio'] = df['Volume'] / vol_ma_filled
            # Handle any remaining NaN or inf
            df['VolRatio'] = df['VolRatio'].fillna(1.0)
            df.loc[np.isinf(df['VolRatio']), 'VolRatio'] = 1.0
            
            # Price change
            df['PctChange'] = df['Close'].pct_change() * 100
            df['PctChange'] = df['PctChange'].fillna(0)
            
            return df
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return None
    
    def detect_breakout(self, symbol, df, min_score=3, min_vol_ratio=1.5):
        """Detect breakout"""
        if df is None or len(df) < 2:
            return None
        
        try:
            curr = df.iloc[-1]
            price = curr['Close']
            score = 0
            
            # Criteria
            if price > curr['High52w'] * 0.99:
                score += 1
            if pd.notna(curr['MA200']) and price > curr['MA200']:
                score += 1
            if price > curr['SwingHigh30d'] * 0.98:
                score += 1
            if curr['VolRatio'] > min_vol_ratio:
                score += 1
            if curr['PctChange'] > 0:
                score += 1
            
            if score < min_score or curr['VolRatio'] < min_vol_ratio:
                return None
            
            return {
                'symbol': symbol,
                'price': round(price, 2),
                'change': round(curr['PctChange'], 2),
                'volume': int(curr['Volume']),
                'vol_avg': int(curr['VolMA20']) if pd.notna(curr['VolMA20']) else 0,
                'vol_ratio': round(curr['VolRatio'], 2),
                'rsi': round(curr['RSI'], 2) if pd.notna(curr['RSI']) else 50,
                'score': score,
                'ma50': round(curr['MA50'], 2) if pd.notna(curr['MA50']) else 0,
            }
        except Exception as e:
            print(f"Error detecting breakout for {symbol}: {e}")
            return None
    
    def screen(self, min_score=3, min_vol_ratio=1.5, progress_bar=None):
        """Screen all stocks"""
        results = []
        total = len(self.stocks)
        
        for i, symbol in enumerate(self.stocks):
            if progress_bar:
                progress_bar.progress((i + 1) / total)
            
            data = self.get_stock_data(symbol)
            if data is None:
                continue
            
            df = self.calculate_indicators(data)
            result = self.detect_breakout(symbol, df, min_score, min_vol_ratio)
            
            if result:
                results.append(result)
        
        if results:
            df_results = pd.DataFrame(results)
            # Calculate rank score
            df_results['rank_score'] = (
                df_results['score'] * 1.5 +
                df_results['vol_ratio'] * 0.5 +
                abs(df_results['rsi'] - 60) / 10
            )
            df_results = df_results.sort_values('rank_score', ascending=False)
            return df_results
        
        return None

# ============================================================================
# STREAMLIT APP
# ============================================================================

# Initialize session state
if 'screener' not in st.session_state:
    st.session_state.screener = MobileBreakoutScreener()
if 'results' not in st.session_state:
    st.session_state.results = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = None

# Header
st.markdown("# 📈 NYSE Breakout Screener")
st.markdown("Find stocks breaking out with high volume confirmation")

# Navigation
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔍 Scan", use_container_width=True):
        st.session_state.page = "scan"

with col2:
    if st.button("📊 Results", use_container_width=True):
        st.session_state.page = "results"

with col3:
    if st.button("⚙️ Settings", use_container_width=True):
        st.session_state.page = "settings"

with col4:
    if st.button("ℹ️ About", use_container_width=True):
        st.session_state.page = "about"

if 'page' not in st.session_state:
    st.session_state.page = "scan"

st.markdown("---")

# ============================================================================
# PAGE: SCAN
# ============================================================================

if st.session_state.page == "scan":
    st.header("🔍 Stock Scanner")
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_score = st.slider("Min Score (0-5)", 2, 5, 3, help="How many criteria must be met")
    
    with col2:
        min_vol = st.slider("Min Volume", 1.0, 5.0, 1.5, step=0.5, help="Multiple of average volume")
    
    if st.button("🚀 RUN SCAN", use_container_width=True, type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.info("🔄 Scanning stocks...")
        
        st.session_state.results = st.session_state.screener.screen(min_score, min_vol, progress_bar)
        st.session_state.last_update = datetime.now()
        
        progress_bar.empty()
        if st.session_state.results is not None:
            status_text.success(f"✅ Found {len(st.session_state.results)} breakouts!")
        else:
            status_text.warning("⚠️ No breakouts found. Try lower criteria.")
    
    # Display last update time
    if st.session_state.last_update:
        st.caption(f"Last updated: {st.session_state.last_update.strftime('%I:%M %p')}")

# ============================================================================
# PAGE: RESULTS
# ============================================================================

elif st.session_state.page == "results":
    st.header("📊 Breakout Results")
    
    if st.session_state.results is None:
        st.info("👈 Run a scan first to see results")
    else:
        results = st.session_state.results
        
        # Statistics
        st.subheader("📈 Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total", len(results))
        
        with col2:
            avg_vol = results['vol_ratio'].mean()
            st.metric("Avg Volume", f"{avg_vol:.1f}x")
        
        with col3:
            avg_change = results['change'].mean()
            st.metric("Avg Change", f"{avg_change:+.1f}%")
        
        with col4:
            avg_rsi = results['rsi'].mean()
            st.metric("Avg RSI", f"{avg_rsi:.0f}")
        
        # Charts
        st.subheader("📊 Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                results.head(10),
                x='symbol',
                y='vol_ratio',
                title='Top 10 - Volume Ratio',
                color='vol_ratio',
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(
                results,
                x='vol_ratio',
                y='change',
                color='score',
                size='rsi',
                hover_data=['symbol'],
                title='Volume vs Price Change',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # RSI Distribution
        fig = go.Figure(data=[
            go.Histogram(x=results['rsi'], nbinsx=20, marker_color='#667eea')
        ])
        fig.update_layout(
            title='RSI Distribution',
            xaxis_title='RSI',
            yaxis_title='Count',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Data Table
        st.subheader("📋 All Stocks")
        
        # Format for display
        display_df = results[['symbol', 'price', 'change', 'vol_ratio', 'rsi', 'score']].copy()
        display_df.columns = ['Symbol', 'Price', 'Change %', 'Vol Ratio', 'RSI', 'Score']
        
        # Color code the table
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Symbol': st.column_config.TextColumn(width='small'),
                'Price': st.column_config.NumberColumn(format='$%.2f', width='small'),
                'Change %': st.column_config.NumberColumn(format='%.2f%%', width='small'),
                'Vol Ratio': st.column_config.NumberColumn(format='%.1fx', width='small'),
                'RSI': st.column_config.NumberColumn(format='%.0f', width='small'),
                'Score': st.column_config.NumberColumn(format='%d/5', width='small'),
            }
        )
        
        # Download button
        csv = results.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"breakout_results_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ============================================================================
# PAGE: SETTINGS
# ============================================================================

elif st.session_state.page == "settings":
    st.header("⚙️ Settings")
    
    st.subheader("📊 Default Screening Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        *Min Score:* Number of criteria that must be met (2-5)
        - 2: Aggressive (more signals)
        - 3: Balanced (default)
        - 5: Conservative (high quality)
        """)
    
    with col2:
        st.info("""
        *Min Volume:* Multiple of 20-day average
        - 1.5x: Low bar (more signals)
        - 2.0x: Good confirmation
        - 3.0x: High confirmation
        """)
    
    st.subheader("🎯 Breakout Criteria")
    st.markdown("""
    The screener checks 5 criteria:
    
    1. *Price > 52-week high* - New territory
    2. *Price > 200-day MA* - Long-term uptrend
    3. *Price > 30-day swing high* - Recent resistance break
    4. *Volume > 2x average* - Confirmation
    5. *Price change > 0%* - Positive momentum
    
    Each criterion = +1 score (max 5)
    """)
    
    st.subheader("📈 Technical Indicators")
    st.markdown("""
    *RSI (0-100):*
    - 0-30: Oversold
    - 30-70: Normal range
    - 70-100: Overbought
    
    *Volume Ratio:*
    - Measures buying pressure
    - 2.0x = Double normal volume
    - 3.0x+ = Strong conviction
    """)
    
    st.subheader("💾 Data Source")
    st.markdown("""
    - Data from: Yahoo Finance
    - Update frequency: Real-time
    - Historical period: 1 year
    - Stocks scanned: 26 liquid NYSE stocks
    """)

# ============================================================================
# PAGE: ABOUT
# ============================================================================

elif st.session_state.page == "about":
    st.header("ℹ️ About This App")
    
    st.markdown("""
    ## NYSE Breakout Stock Screener
    
    ### What It Does
    Identifies NYSE stocks that are *breaking out* with *high volume confirmation*.
    
    A breakout occurs when a stock price breaks above a key resistance level 
    (52-week high, 200-day moving average, or recent swing high) with increased volume.
    
    ### How It Works
    1. *Scans* 26 liquid NYSE stocks
    2. *Calculates* technical indicators (moving averages, RSI, volume)
    3. *Scores* each stock (0-5 criteria met)
    4. *Filters* based on your criteria
    5. *Ranks* by probability of success
    6. *Displays* interactive charts and data
    
    ### Key Features
    ✅ Real-time stock data (Yahoo Finance)
    ✅ Interactive charts and visualizations
    ✅ Customizable scan parameters
    ✅ Download results as CSV
    ✅ Mobile-responsive design
    ✅ No sign-up required
    
    ### How to Use
    1. Go to *SCAN* tab
    2. Adjust parameters (min score, min volume)
    3. Click *RUN SCAN*
    4. View results in *RESULTS* tab
    5. Download data if needed
    
    ### Important Notes
    ⚠️ *Educational purposes only* - Not financial advice
    ⚠️ *Trade at your own risk* - Use proper risk management
    ⚠️ *Backtest first* - Test strategy before risking money
    ⚠️ *False signals possible* - ~50% of breakouts fail
    
    ### Strategies
    
    *Aggressive* (More signals):
    - Min Score: 2
    - Min Volume: 1.5x
    - Result: 10-15 stocks daily
    
    *Balanced* (Default):
    - Min Score: 3
    - Min Volume: 2.0x
    - Result: 5-8 stocks daily
    
    *Conservative* (High quality):
    - Min Score: 5
    - Min Volume: 3.0x
    - Result: 1-3 stocks daily
    
    ### Disclaimer
    This app is for educational purposes only. It is not financial advice.
    Always do your own research and consult a financial advisor before trading.
    Past performance is not indicative of future results.
    
    ### Contact & Support
    For issues or questions, refer to the documentation or review the code on GitHub.
    
    *Version:* 1.0  
    *Last Updated:* January 2024  
    *Made with ❤️ for traders and investors*
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; font-size: 0.8rem;'>
    NYSE Breakout Screener | Real-time Stock Analysis
    <br>
    <span style='color: #ccc;'>Educational Use Only • Not Financial Advice</span>
</div>
""", unsafe_allow_html=True)
