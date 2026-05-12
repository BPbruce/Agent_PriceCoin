from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
COINGECKO_COINS_LIST_URL = "https://api.coingecko.com/api/v3/coins/list"
REQUEST_TIMEOUT = 10

# 缓存支持的币种
coins_cache = {}


def get_supported_coins():
    """获取支持的币种列表"""
    if not coins_cache:
        try:
            response = requests.get(COINGECKO_COINS_LIST_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            coins_data = response.json()
            coins_cache.update({coin["id"]: coin["name"] for coin in coins_data})
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch supported coins from CoinGecko.")
    return coins_cache


@app.get("/")
def read_root():
    return {"message": "Welcome to the Crypto Price API! Use /price endpoint to get prices."}


@app.get("/price/")
def get_crypto_price(coin: str, currency: str = "usd"):
    """获取加密货币的实时价格"""
    supported_coins = get_supported_coins()

    if coin not in supported_coins:
        raise HTTPException(
            status_code=404,
            detail=f"币种 '{coin}' 不支持。支持的币种ID请访问 /coins/ 端点查看。",
        )

    try:
        response = requests.get(
            COINGECKO_API_URL,
            params={"ids": coin, "vs_currencies": currency},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"从 CoinGecko 获取价格失败: {str(e)}")

    if coin not in data or currency not in data[coin]:
        raise HTTPException(status_code=404, detail=f"在 API 响应中未找到 '{coin}' 的价格数据")

    return {"coin": supported_coins[coin], "price": data[coin][currency], "currency": currency}


@app.get("/coins/")
def get_coins():
    """列出支持的币种"""
    return {"supported_coins": get_supported_coins()}
