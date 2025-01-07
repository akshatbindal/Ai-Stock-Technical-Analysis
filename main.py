import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import base64
import google.generativeai as genai

# Set up Streamlit app
st.set_page_config(layout="wide")
st.title("AI-Powered Technical Stock Analysis Dashboard")
st.sidebar.header("Configuration")

# Input for stock ticker and date range
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL):", "AAPL")
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2024-12-14"))

# Fetch stock data
if st.sidebar.button("Fetch Data"):
    st.session_state["stock_data"] = yf.download(ticker, start=start_date, end=end_date)
    st.success("Stock data loaded successfully!")

# Check if data is available
if "stock_data" in st.session_state:
    data = st.session_state["stock_data"]

    # Plot candlestick chart
    fig = go.Figure(data=[
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Candlestick"
        )
    ])

    # Sidebar: Select technical indicators
    st.sidebar.subheader("Technical Indicators")
    indicators = st.sidebar.multiselect(
        "Select Indicators:",
        ["20-Day SMA", "20-Day EMA", "20-Day Bollinger Bands", "VWAP"],
        default=["20-Day SMA"]
    )

    # Helper function to add indicators to the chart
    def add_indicator(indicator):
        if indicator == "20-Day SMA":
            sma = data['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(x=data.index, y=sma, mode='lines', name='SMA (20)'))
        elif indicator == "20-Day EMA":
            ema = data['Close'].ewm(span=20).mean()
            fig.add_trace(go.Scatter(x=data.index, y=ema, mode='lines', name='EMA (20)'))
        elif indicator == "20-Day Bollinger Bands":
            sma = data['Close'].rolling(window=20).mean()
            std = data['Close'].rolling(window=20).std()
            bb_upper = sma + 2 * std
            bb_lower = sma - 2 * std
            fig.add_trace(go.Scatter(x=data.index, y=bb_upper, mode='lines', name='BB Upper'))
            fig.add_trace(go.Scatter(x=data.index, y=bb_lower, mode='lines', name='BB Lower'))
        elif indicator == "VWAP":
            data['VWAP'] = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
            fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'], mode='lines', name='VWAP'))

    # Add selected indicators to the chart
    for indicator in indicators:
        add_indicator(indicator)

    fig.update_layout(xaxis_rangeslider_visible=False)
    st.plotly_chart(fig)

    # Analyze chart with Gemini API
    st.subheader("AI-Powered Analysis")
    if st.button("Run AI Analysis"):
        with st.spinner("Analyzing the chart, please wait..."):
            try:
                # Convert chart to image bytes
                image_bytes = fig.to_image(format="png")
                # Encode image to Base64
                image_data = base64.b64encode(image_bytes).decode('utf-8')
                    
                # Prepare Gemini API request
                api_key = st.secrets["api"]["key"]
                if not api_key:
                    st.error("API key for Gemini is not set. Please set the GEMINI_API_KEY environment variable.")
                    st.stop()
                genai.configure(api_key=api_key)
                gemini_model = genai.GenerativeModel("gemini-1.5-flash") 

                prompt = """You are a Stock Trader specializing in Technical Analysis at a top financial institution. 
                Analyze the stock chart's technical indicators and provide a buy/hold/sell recommendation. 
                Base your recommendation only on the candlestick chart and the displayed technical indicators. 
                First, provide the recommendation, then provide your detailed reasoning."""

                response = gemini_model.generate_content(
                    [
                        {
                            "mime_type": "image/png",
                            "data": image_data,
                        },
                        prompt,
                    ]
                )

                # Display AI analysis result
                st.write("**AI Analysis Results:**")
                st.write(response.text)

            except Exception as e:
                st.error(f"An error occurred: {e}")