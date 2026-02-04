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

def get_recent_trades(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/trades?symbol={symbol}&limit=15"
    try:
        data = requests.get(url, timeout=5).json()
        df = pd.DataFrame(data)
        df['time'] = pd.to_datetime(df['time'], unit='ms').dt.strftime('%H:%M:%S')
        df['price'] = df['price'].astype(float)
        df['qty'] = df['qty'].astype(float)
        return df[['time', 'price', 'qty']]
    except Exception:
        return None

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

# --- ПЕРСОНАЛІЗАЦІЯ В SIDEBAR ---
st.sidebar.divider()
st.sidebar.subheader("⭐ Мій Watchlist")
selected_watch = st.sidebar.multiselect(
    "Стежити за:", 
    ["ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"],
    default=["ETHUSDT"]
)
watchlist_placeholder = st.sidebar.empty()

st.sidebar.divider()
st.sidebar.subheader("🎨 Налаштування графіку")
chart_type = st.sidebar.radio("Тип графіка", ["Лінійний", "З областями"])
show_volume = st.sidebar.toggle("Показувати об'єми торгів", value=True)

st.sidebar.divider()
st.sidebar.subheader("🚀 Рівень ризику")
risk_profile = st.sidebar.select_slider(
    "Ваш профіль:",
    options=["Консервативний", "Помірний", "Агресивний"]
)
if risk_profile == "Агресивний":
    st.sidebar.warning("Будьте обережні з великим плечем!")

st.sidebar.divider()
st.sidebar.subheader("🔗 Швидкі посилання")
st.sidebar.markdown("""
- [Binance Exchange](https://www.binance.com)
- [CoinMarketCap](https://coinmarketcap.com)
- [TradingView Charts](https://www.tradingview.com)
""")

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
        with t_col1:
            st.button(f"КУПИТИ {symbol[:-4]}", use_container_width=True, type="primary")
            st.number_input("Ціна входу", value=0.0, key="buy_price", format="%.4f")
        with t_col2:
            st.button(f"ПРОДАТИ {symbol[:-4]}", use_container_width=True)
            st.number_input("Кількість", value=0.0, key="trade_qty", format="%.4f")
        
        st.divider()
        st.markdown("### 📑 Склянка ордерів (Order Book)")
        ob_col1, ob_col2 = st.columns(2)
        bids_placeholder = ob_col1.empty()
        asks_placeholder = ob_col2.empty()

    with col_side:
        st.subheader("📰 Новини")
        news_placeholder = st.empty()
        st.divider()
        st.subheader("🕒 Останні угоди")
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
    whale_data = pd.DataFrame({
        'Час': [datetime.now().strftime("%H:%M:%S")],
        'Актив': [symbol[:-4]], 'Сума': ["$4,150,000"],
        'Джерело': ["Unknown Wallet"], 'Призначення': ["Binance"], 'Тип': ["🚨 Вливання"]
    })
    st.table(whale_data)

# --- ЛОГІКА ОНОВЛЕННЯ ---

if 'current_symbol' not in st.session_state or st.session_state.current_symbol != symbol:
    st.session_state.price_history, st.session_state.time_history = [], []
    st.session_state.current_symbol = symbol

try:
    while True:
        data = get_binance_ticker(symbol)
        bids, asks = get_order_book(symbol)
        recent_trades = get_recent_trades(symbol)
        
        # Оновлення Watchlist у сайдбарі
        with watchlist_placeholder.container():
            for coin in selected_watch:
                c_data = get_binance_ticker(coin)
                if c_data:
                    st.write(f"**{coin}**: ${float(c_data['lastPrice']):,.2f} ({c_data['priceChangePercent']}%)")

        if data and 'lastPrice' in data:
            price = float(data['lastPrice'])
            calc_placeholder.write(f"Орієнтовний об'єм: **{(usd_amount * lever) / price:.5f} {symbol[:-4]}**")

            with metrics_placeholder.container():
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Ціна", f"${price:,.2f}", f"{data['priceChangePercent']}%")
                m2.metric("Об'єм 24г", f"{float(data['volume']):,.0f} {symbol[:-4]}")
                m3.metric("Макс 24г", f"${float(data['highPrice']):,.2f}")
                m4.metric("Мін 24г", f"${float(data['lowPrice']):,.2f}")

            st.session_state.price_history.append(price)
            st.session_state.time_history.append(datetime.now())
            if len(st.session_state.price_history) > 30:
                st.session_state.price_history.pop(0)
                st.session_state.time_history.pop(0)

            # Налаштування графіка згідно з вибором у Sidebar
            fig = go.Figure()
            fill_mode = 'tozeroy' if chart_type == "З областями" else None
            fig.add_trace(go.Scatter(x=st.session_state.time_history, y=st.session_state.price_history, 
                                     mode='lines+markers', line=dict(color='#00FFCC'), fill=fill_mode))
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=10), template="plotly_dark")
            chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"c_{symbol}_{time.time()}")

            if bids is not None:
                bids_placeholder.dataframe(bids.style.format(precision=2).background_gradient(cmap='Greens', subset=['Quantity']), use_container_width=True)
                asks_placeholder.dataframe(asks.style.format(precision=2).background_gradient(cmap='Reds', subset=['Quantity']), use_container_width=True)

            if recent_trades is not None:
                trades_placeholder.dataframe(recent_trades, use_container_width=True, height=300, hide_index=True)

            with news_placeholder.container():
                for item in get_crypto_news()[:4]:
                    st.markdown(f"**[{item['title']}]({item['url']})**")
                    st.divider()

        time.sleep(update_speed)
except Exception as e:
    st.error(f"Помилка: {e}")
