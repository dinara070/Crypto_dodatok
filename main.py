import asyncio
import ccxt.pro as ccxtpro  # Асинхронна бібліотека для бірж
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import aiohttp

app = FastAPI()

# Дозволяємо підключення з фронтенду
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Ендпоінт для отримання новин (Агрегатор)
@app.get("/api/news")
async def get_crypto_news():
    url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            # Повертаємо тільки останні 5 новин
            return data.get("Data", [])[:5]

# 2. WebSocket для трансляції цін у реальному часі
@app.websocket("/ws/ticker/{symbol}")
async def websocket_ticker(websocket: WebSocket, symbol: str):
    await websocket.accept()
    # Ініціалізуємо підключення до Binance через CCXT
    exchange = ccxtpro.binance()
    
    try:
        while True:
            # Отримуємо дані про ціну (Ticker) в реальному часі
            ticker = await exchange.watch_ticker(symbol.upper())
            await websocket.send_json({
                "symbol": ticker['symbol'],
                "price": ticker['last'],
                "high": ticker['high'],
                "low": ticker['low'],
                "change": ticker['percentage']
            })
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await exchange.close()
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
