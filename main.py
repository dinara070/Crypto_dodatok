import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import plotly.graph_objects as go

# Налаштування сторінки
st.set_page_config(page_title="Crypto Trading Portal Pro", layout="wide")

# --- ФУНКЦІЇ ДЛЯ ДАНИХ ---

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
        return requests.get(url, timeout=5).json()
    except Exception:
        return None

def get_order_book(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=10"
    try:
        data = requests.get(url, timeout=5).json()
        bids = pd.DataFrame(data['bids'], columns=['Price', 'Quantity']).astype(float)
        asks = pd.DataFrame(data['asks'], columns=['Price', 'Quantity']).astype(float)
        return bids, asks
    except Exception:
        return None, None

# --- БОКОВА ПАНЕЛЬ (SIDEBAR) ---
st.sidebar.header("⚙️ Налаштування та Інструменти")
symbol = st.sidebar.selectbox("Оберіть торгову пару", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"])
update_speed = st.sidebar.slider("Оновлення (сек)", 2, 10, 3)

st.sidebar.divider()
st.sidebar.subheader("🧮 Калькулятор прибутку")
usd_amount = st.sidebar.number_input("Сума в USDT", min_value=10, value=100)
lever = st.sidebar.select_slider("Плече (leverage)", options=[1, 2, 5, 10, 20])

st.sidebar.divider()
st.sidebar.subheader("📊 Статус ринку")
st.sidebar.info("Fear & Greed Index: 65 (Greed)") # Можна підключити API index

# --- ОСНОВНИЙ ІНТЕРФЕЙС ---
st.title("🚀 Crypto Intelligence & Trading Portal")

col_main, col_news = st.columns([3, 1])

with col_main:
    # Верхній ряд метрик
    metrics_placeholder = st.empty()
    
    # Графік
    st.markdown("### 📈 Живий графік")
    chart_placeholder = st.empty()
    
    # Нова секція: Order Book
    st.markdown("### 📑 Склянка ордерів (Order Book)")
    col_bids, col_asks = st.columns(2)
    with col_bids:
        st.caption("Покупці (Bids)")
        bids_placeholder = st.empty()
    with col_asks:
        st.caption("Продавці (Asks)")
        asks_placeholder = st.empty()

with col_news:
    st.subheader("📰 Останні новини")
    news_placeholder = st.empty()

# --- ЛОГІКА ОНОВЛЕННЯ ---

# Скидання історії при зміні символу
if 'current_symbol' not in st.session_state or st.session_state.current_symbol != symbol:
    st.session_state.price_history = []
    st.session_state.time_history = []
    st.session_state.current_symbol = symbol

try:
    while True:
        data = get_binance_ticker(symbol)
        bids, asks = get_order_book(symbol)
        
        if data and 'lastPrice' in data:
            current_price = float(data['lastPrice'])
            
            # Калькулятор (динамічне оновлення в Sidebar)
            potential_coins = (usd_amount * lever) / current_price
            st.sidebar.write(f"Ви можете купити: **{potential_coins:.5f} {symbol[:-4]}**")

            # 1. Оновлення метрик
            with metrics_placeholder.container():
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Ціна", f"${current_price:,.2f}", f"{data['priceChangePercent']}%")
                m2.metric("Об'єм 24г", f"{float(data['volume']):,.0f} {symbol[:-4]}")
                m3.metric("Макс 24г", f"${float(data['highPrice']):,.2f}")
                m4.metric("Мін 24г", f"${float(data['lowPrice']):,.2f}")

            # 2. Оновлення графіка
            st.session_state.price_history.append(current_price)
            st.session_state.time_history.append(datetime.now())
            if len(st.session_state.price_history) > 30:
                st.session_state.price_history.pop(0)
                st.session_state.time_history.pop(0)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=st.session_state.time_history, y=st.session_state.price_history, 
                                     mode='lines+markers', line=dict(color='#00FFCC')))
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=10), template="plotly_dark")
            chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"chart_{symbol}")

            # 3. Оновлення Order Book
            if bids is not None and asks is not None:
                bids_placeholder.dataframe(bids, use_container_width=True, height=250)
                asks_placeholder.dataframe(asks, use_container_width=True, height=250)

            # 4. Оновлення Новин (раз на цикл, щоб не миготіли)
            with news_placeholder.container():
                news = get_crypto_news()
                for item in news[:4]:
                    st.markdown(f"**{item['title']}**")
                    st.caption(f"{datetime.fromtimestamp(item['published_on']).strftime('%H:%M')}")
                    st.divider()

        time.sleep(update_speed)

except Exception as e:
    st.error(f"Системна помилка: {e}")
