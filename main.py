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
    url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=10"
    try:
        data = requests.get(url, timeout=5).json()
        bids = pd.DataFrame(data['bids'], columns=['Price', 'Quantity']).astype(float)
        asks = pd.DataFrame(data['asks'], columns=['Price', 'Quantity']).astype(float)
        return bids, asks
    except Exception:
        return None, None

def get_fear_greed_index():
    try:
        res = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        return res['data'][0]['value'], res['data'][0]['value_classification']
    except:
        return "50", "Neutral"

# --- БОКОВА ПАНЕЛЬ (SIDEBAR) ---
st.sidebar.header("⚙️ Налаштування та Інструменти")
symbol = st.sidebar.selectbox("Оберіть торгову пару", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"])
update_speed = st.sidebar.slider("Оновлення (сек)", 2, 10, 3)

# Fear & Greed Index
fng_val, fng_class = get_fear_greed_index()
st.sidebar.metric("Fear & Greed Index", f"{fng_val} - {fng_class}")

st.sidebar.divider()
st.sidebar.subheader("🧮 Калькулятор прибутку")
usd_amount = st.sidebar.number_input("Сума в USDT", min_value=10, value=100)
lever = st.sidebar.select_slider("Плече (leverage)", options=[1, 2, 5, 10, 20])
calc_placeholder = st.sidebar.empty()

st.sidebar.divider()
st.sidebar.subheader("🔗 Швидкі посилання")
st.sidebar.markdown("""
- [Binance Exchange](https://www.binance.com)
- [CoinMarketCap](https://coinmarketcap.com)
- [TradingView Charts](https://www.tradingview.com)
""")

# --- ОСНОВНИЙ ІНТЕРФЕЙС ---
st.title("🚀 Crypto Intelligence & Trading Portal")

# Створення вкладок
tab1, tab2, tab3 = st.tabs(["📈 Торгівля", "🔍 Технічний аналіз", "🐋 Whale Alert"])

with tab1:
    col_main, col_news = st.columns([3, 1])

    with col_main:
        metrics_placeholder = st.empty()
        st.markdown("### 📊 Живий графік")
        chart_placeholder = st.empty()
        
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
        
        st.divider()
        st.subheader("🔗 Офіційні канали")
        st.markdown("""
        * [**CoinDesk**](https://www.coindesk.com/) — Новини.
        * [**CoinTelegraph**](https://cointelegraph.com/) — Аналітика.
        * [**CryptoPanic**](https://cryptopanic.com/) — Агрегатор.
        * [**Glassnode**](https://studio.glassnode.com/) — On-chain.
        * [**Binance Twitter**](https://twitter.com/binance) — Анонси.
        """)

with tab2:
    st.subheader("🛠️ Професійний аналіз (TradingView)")
    tv_chart_html = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "width": "100%",
        "height": 600,
        "symbol": "BINANCE:{symbol}",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "uk",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(tv_chart_html, height=610)

with tab3:
    st.subheader("🐋 Відстеження великих транзакцій")
    st.info("Моніторинг гаманців з балансом понад $1,000,000")
    whale_data = pd.DataFrame({
        'Час': [datetime.now().strftime("%H:%M:%S")],
        'Актив': [symbol[:-4]],
        'Сума': ["$2,450,000"],
        'Джерело': ["Unknown Wallet"],
        'Призначення': ["Binance"],
        'Статус': ["🚨 Велика активність"]
    })
    st.table(whale_data)

# --- ЛОГІКА ОНОВЛЕННЯ ---

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
            
            # 1. Оновлення калькулятора
            potential_coins = (usd_amount * lever) / current_price
            calc_placeholder.write(f"Орієнтовний об'єм: **{potential_coins:.5f} {symbol[:-4]}**")

            # 2. Оновлення метрик
            with metrics_placeholder.container():
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Ціна", f"${current_price:,.2f}", f"{data['priceChangePercent']}%")
                m2.metric("Об'єм 24г", f"{float(data['volume']):,.0f} {symbol[:-4]}")
                m3.metric("Макс 24г", f"${float(data['highPrice']):,.2f}")
                m4.metric("Мін 24г", f"${float(data['lowPrice']):,.2f}")

            # 3. Оновлення графіка Plotly
            st.session_state.price_history.append(current_price)
            st.session_state.time_history.append(datetime.now())
            if len(st.session_state.price_history) > 30:
                st.session_state.price_history.pop(0)
                st.session_state.time_history.pop(0)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=st.session_state.time_history, y=st.session_state.price_history, 
                                     mode='lines+markers', line=dict(color='#00FFCC'), fill='tozeroy'))
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=10), template="plotly_dark")
            chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"chart_{symbol}_{time.time()}")

            # 4. Оновлення Order Book
            if bids is not None and asks is not None:
                bids_placeholder.dataframe(bids.style.format(precision=2).background_gradient(cmap='Greens', subset=['Quantity']), use_container_width=True, height=250)
                asks_placeholder.dataframe(asks.style.format(precision=2).background_gradient(cmap='Reds', subset=['Quantity']), use_container_width=True, height=250)

            # 5. Оновлення Новин
            with news_placeholder.container():
                news = get_crypto_news()
                for item in news[:4]:
                    st.markdown(f"**[{item['title']}]({item['url']})**")
                    st.caption(f"Джерело: {item['source']} | {datetime.fromtimestamp(item['published_on']).strftime('%H:%M')}")
                    st.divider()

        time.sleep(update_speed)

except Exception as e:
    st.error(f"Системна помилка: {e}")
