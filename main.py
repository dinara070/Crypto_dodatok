import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import plotly.graph_objects as go

# Налаштування сторінки
st.set_page_config(page_title="Crypto Trading Portal", layout="wide")

# --- ФУНКЦІЇ ДЛЯ ДАНИХ ---

def get_crypto_news():
    """Отримання свіжих новин криптовалют"""
    url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
    try:
        response = requests.get(url, timeout=5)
        return response.json().get("Data", [])[:5]
    except:
        return []

def get_binance_ticker(symbol="BTCUSDT"):
    """Отримання поточної ціни та статистики через REST API (для стабільності)"""
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    try:
        return requests.get(url).json()
    except:
        return None

# --- ІНТЕРФЕЙС ---

st.title("🚀 Crypto Intelligence & Trading Portal")

# Сайдбар для налаштувань
symbol = st.sidebar.selectbox("Оберіть торгову пару", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"])
update_speed = st.sidebar.slider("Швидкість оновлення (сек)", 1, 10, 2)

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"Графік {symbol}")
    
    # Контейнер для "живих" метрик, щоб не було помилок removeChild
    metrics_placeholder = st.empty()
    
    # Симуляція графіка (використання Plotly для професійного вигляду)
    # У реальному проекті тут підключається TradingView Lightweight Charts
    chart_placeholder = st.empty()

with col2:
    st.subheader("Останні новини")
    news = get_crypto_news()
    for item in news:
        st.markdown(f"**[{item['title']}]({item['url']})**")
        st.caption(f"Джерело: {item['source']} | {datetime.fromtimestamp(item['published_on']).strftime('%H:%M')}")
        st.divider()

# --- ЦИКЛ ОНОВЛЕННЯ ДАНИХ ---

while True:
    data = get_binance_ticker(symbol)
    
    if data:
        # Оновлюємо метрики в окремому контейнері
        with metrics_placeholder.container():
            m1, m2, m3 = st.columns(3)
            m1.metric("Ціна", f"${float(data['lastPrice']):,.2f}", f"{data['priceChangePercent']}%")
            m2.metric("Макс за 24г", f"${float(data['highPrice']):,.2f}")
            m3.metric("Мін за 24г", f"${float(data['lowPrice']):,.2f}")

        # Малюємо простий свічковий графік (приклад)
        # Для реальної біржі тут краще використовувати st.components.v1.html з TradingView
        fig = go.Figure(data=[go.Scatter(x=[datetime.now()], y=[float(data['lastPrice'])], mode='lines+markers')])
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
        chart_placeholder.plotly_chart(fig, use_container_width=True)

    time.sleep(update_speed)
