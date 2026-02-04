import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import plotly.graph_objects as go
import streamlit.components.v1 as components

# Налаштування сторінки
st.set_page_config(page_title="Crypto Portal Pro", layout="wide", page_icon="🚀")

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
        res = requests.get(url, timeout=5)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None

def get_order_book(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=15"
    try:
        data = requests.get(url, timeout=5).json()
        bids = pd.DataFrame(data['bids'], columns=['Price', 'Quantity']).astype(float)
        asks = pd.DataFrame(data['asks'], columns=['Price', 'Quantity']).astype(float)
        return bids, asks
    except Exception:
        return None, None

def get_recent_trades(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/trades?symbol={symbol}&limit=20"
    try:
        data = requests.get(url, timeout=5).json()
        df = pd.DataFrame(data)
        df['time'] = pd.to_datetime(df['time'], unit='ms').dt.strftime('%H:%M:%S')
        df['price'] = df['price'].astype(float)
        df['qty'] = df['qty'].astype(float)
        # Визначаємо сторону угоди (імітація для візуалізації)
        df['Side'] = df['isBuyerMaker'].apply(lambda x: "SELL" if x else "BUY")
        return df[['time', 'price', 'qty', 'Side']]
    except Exception:
        return None

def get_fear_greed_index():
    try:
        res = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        return res['data'][0]['value'], res['data'][0]['value_classification']
    except:
        return "50", "Neutral"

# --- БОКОВА ПАНЕЛЬ ---
st.sidebar.header("⚙️ Налаштування та Інструменти")
symbol = st.sidebar.selectbox("Оберіть торгову пару", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"])
update_speed = st.sidebar.slider("Оновлення (сек)", 2, 10, 3)

fng_val, fng_class = get_fear_greed_index()
st.sidebar.metric("Fear & Greed Index", f"{fng_val} - {fng_class}")

st.sidebar.divider()
st.sidebar.subheader("🧮 Калькулятор прибутку")
usd_amount = st.sidebar.number_input("Сума в USDT", min_value=10, value=100)
lever = st.sidebar.select_slider("Плече (leverage)", options=[1, 2, 5, 10, 20])
calc_placeholder = st.sidebar.empty()

st.sidebar.divider()
st.sidebar.subheader("⭐ Мій Watchlist")
selected_watch = st.sidebar.multiselect("Стежити за:", ["ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"], default=["ETHUSDT"])
watchlist_placeholder = st.sidebar.empty()

st.sidebar.divider()
st.sidebar.subheader("🎨 Налаштування графіку")
chart_type = st.sidebar.radio("Тип графіка", ["Лінійний", "З областями"])

# --- ОСНОВНИЙ ІНТЕРФЕЙС ---
st.title("🚀 Crypto Intelligence & Trading Portal")
tab1, tab2, tab3 = st.tabs(["📈 Торгівля", "🔍 Технічний аналіз", "🐋 Whale Alert"])

with tab1:
    col_main, col_side = st.columns([2, 1])
    with col_main:
        metrics_placeholder = st.empty()
        st.markdown("### 📊 Живий графік")
        chart_placeholder = st.empty()
        
        st.markdown("### ⚡ Швидка торгівля (Simulation)")
        t_col1, t_col2 = st.columns(2)
        t_col1.button(f"КУПИТИ {symbol[:-4]}", key="btn_buy", use_container_width=True, type="primary")
        t_col2.button(f"ПРОДАТИ {symbol[:-4]}", key="btn_sell", use_container_width=True)
        
        st.divider()
        st.markdown("### 📑 Склянка ордерів (Order Book)")
        # Додаємо візуалізацію глибини ринку
        ob_col1, ob_col2 = st.columns(2)
        bids_placeholder = ob_col1.empty()
        asks_placeholder = ob_col2.empty()

    with col_side:
        st.subheader("📰 Новини")
        news_placeholder = st.empty()
        st.divider()
        st.subheader("🕒 Останні угоди")
        # Тут будемо використовувати кольорове маркування для BUY/SELL
        trades_placeholder = st.empty()

with tab2:
    st.subheader("🛠️ Професійний аналіз (TradingView)")
    tv_chart_html = f"""
    <div style="height:600px;"><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">new TradingView.widget({{"width": "100%", "height": 600, "symbol": "BINANCE:{symbol}",
    "interval": "D", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "uk", "container_id": "tv_chart"}});
    </script><div id="tv_chart"></div></div>
    """
    components.html(tv_chart_html, height=610)

with tab3:
    st.subheader("🐋 Відстеження великих транзакцій")
    whale_placeholder = st.empty()

# --- ЛОГІКА ОНОВЛЕННЯ ---

if 'current_symbol' not in st.session_state or st.session_state.current_symbol != symbol:
    st.session_state.price_history, st.session_state.time_history = [], []
    st.session_state.current_symbol = symbol

try:
    while True:
        data = get_binance_ticker(symbol)
        bids, asks = get_order_book(symbol)
        recent_trades = get_recent_trades(symbol)
        
        # 1. Оновлення Watchlist
        with watchlist_placeholder.container():
            for coin in selected_watch:
                cw = get_binance_ticker(coin)
                if cw: st.write(f"**{coin}**: ${float(cw['lastPrice']):,.2f} ({cw['priceChangePercent']}%)")

        if data:
            current_price = float(data['lastPrice'])
            calc_placeholder.write(f"Орієнтовний об'єм: **{(usd_amount * lever) / current_price:.5f} {symbol[:-4]}**")

            # 2. Метрики
            with metrics_placeholder.container():
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Ціна", f"${current_price:,.2f}", f"{data['priceChangePercent']}%")
                m2.metric("Об'єм 24г", f"{float(data['volume']):,.0f}")
                m3.metric("Макс 24г", f"${float(data['highPrice']):,.2f}")
                m4.metric("Мін 24г", f"${float(data['lowPrice']):,.2f}")

            # 3. Графік
            st.session_state.price_history.append(current_price)
            st.session_state.time_history.append(datetime.now())
            if len(st.session_state.price_history) > 30:
                st.session_state.price_history.pop(0)
                st.session_state.time_history.pop(0)

            fig = go.Figure()
            f_mode = 'tozeroy' if chart_type == "З областями" else None
            fig.add_trace(go.Scatter(x=st.session_state.time_history, y=st.session_state.price_history, 
                                     mode='lines+markers', line=dict(color='#00FFCC'), fill=f_mode))
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=10), template="plotly_dark")
            chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"c_{time.time()}")

            # 4. Склянка (Order Book) з покращеною візуалізацією
            if bids is not None and asks is not None:
                # Додаємо стовпчик сукупного об'єму для "барів"
                bids['Total'] = bids['Quantity'].cumsum()
                asks['Total'] = asks['Quantity'].cumsum()
                
                bids_placeholder.dataframe(
                    bids.style.format(precision=2).bar(subset=['Quantity'], color='#005522')
                    .background_gradient(cmap='Greens', subset=['Price']), 
                    use_container_width=True, height=400
                )
                asks_placeholder.dataframe(
                    asks.style.format(precision=2).bar(subset=['Quantity'], color='#550022')
                    .background_gradient(cmap='Reds', subset=['Price']), 
                    use_container_width=True, height=400
                )

            # 5. Останні угоди з кольоровим маркуванням
            if recent_trades is not None:
                def color_side(val):
                    color = '#00ff00' if val == "BUY" else '#ff0000'
                    return f'color: {color}; font-weight: bold'
                
                trades_placeholder.dataframe(
                    recent_trades.style.applymap(color_side, subset=['Side']).format(precision=4),
                    use_container_width=True, height=400, hide_index=True
                )

            # 6. Новини
            with news_placeholder.container():
                for item in get_crypto_news()[:4]:
                    st.markdown(f"**[{item['title']}]({item['url']})**")
                    st.divider()

        time.sleep(update_speed)
except Exception as e:
    st.error(f"Помилка: {e}")
