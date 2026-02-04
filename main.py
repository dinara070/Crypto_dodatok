import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import plotly.graph_objects as go

# Налаштування сторінки
st.set_page_config(page_title="Crypto Trading Portal", layout="wide")

# Використовуємо кешування, щоб не робити зайвих запитів при кожному оновленні інтерфейсу
@st.cache_data(ttl=60)
def get_crypto_news():
    url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
    try:
        response = requests.get(url, timeout=5)
        return response.json().get("Data", [])[:5]
    except Exception:
        return []

def get_binance_ticker(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    try:
        response = requests.get(url, timeout=5)
        return response.json()
    except Exception:
        return None

# --- ІНТЕРФЕЙС ---
st.title("🚀 Crypto Intelligence & Trading Portal")

# Сайдбар
symbol = st.sidebar.selectbox("Оберіть торгову пару", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"])
update_speed = st.sidebar.slider("Швидкість оновлення (сек)", 2, 10, 3) # Мінімум 2 сек для стабільності

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"Графік {symbol}")
    # Створюємо статичні контейнери ОДИН РАЗ
    metrics_placeholder = st.empty()
    chart_placeholder = st.empty()

with col2:
    st.subheader("Останні новини")
    news_container = st.container()
    with news_container:
        news = get_crypto_news()
        if news:
            for item in news:
                st.markdown(f"**[{item['title']}]({item['url']})**")
                st.caption(f"Джерело: {item['source']} | {datetime.fromtimestamp(item['published_on']).strftime('%H:%M')}")
                st.divider()
        else:
            st.write("Новини тимчасово недоступні")

# --- ЦИКЛ ОНОВЛЕННЯ ДАНИХ ---
# Список для зберігання історії цін для графіка
if 'price_history' not in st.session_state:
    st.session_state.price_history = []
    st.session_state.time_history = []

try:
    while True:
        data = get_binance_ticker(symbol)
        
        if data and 'lastPrice' in data:
            current_price = float(data['lastPrice'])
            current_time = datetime.now()

            # Оновлюємо історію (зберігаємо останні 20 точок)
            st.session_state.price_history.append(current_price)
            st.session_state.time_history.append(current_time)
            if len(st.session_state.price_history) > 20:
                st.session_state.price_history.pop(0)
                st.session_state.time_history.pop(0)

            # 1. Оновлюємо метрики
            with metrics_placeholder.container():
                m1, m2, m3 = st.columns(3)
                m1.metric("Ціна", f"${current_price:,.2f}", f"{data['priceChangePercent']}%")
                m2.metric("Макс 24г", f"${float(data['highPrice']):,.2f}")
                m3.metric("Мін 24г", f"${float(data['lowPrice']):,.2f}")

            # 2. Оновлюємо графік
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=st.session_state.time_history, 
                y=st.session_state.price_history,
                mode='lines+markers',
                line=dict(color='#00ff00', width=2),
                fill='tozeroy'
            ))
            fig.update_layout(
                height=400, 
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_title="Час",
                yaxis_title="Ціна (USDT)"
            )
            chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"chart_{symbol}")

        # Пауза
        time.sleep(update_speed)

except Exception as e:
    st.error(f"Виникла помилка: {e}. Спробуйте перезавантажити сторінку.")
