import json
import os
import time

import requests

# 配置
GPT_API_URL = "https://yunwu.ai/v1/chat/completions"
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("YUNWU_API_KEY", "")
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/list"

REQUEST_TIMEOUT = 10
UPDATE_INTERVAL = 3600  # 每小时更新一次

# 缓存代币映射
token_mappings = {}
valid_token_ids = set()
last_update_time = 0


def _build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


def update_token_mappings():
    """
    从 CoinGecko 获取最新的代币列表并更新映射
    """
    global last_update_time

    current_time = time.time()
    if current_time - last_update_time < UPDATE_INTERVAL and token_mappings:
        return token_mappings

    try:
        print("正在从 CoinGecko 更新代币列表...")
        response = requests.get(COINGECKO_API_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        coins_data = response.json()

        # 清空旧的映射
        token_mappings.clear()
        valid_token_ids.clear()

        # 为每个代币创建映射
        for coin in coins_data:
            coin_id = coin["id"]
            valid_token_ids.add(coin_id)
            token_mappings[coin["symbol"].upper()] = coin_id
            token_mappings[coin["name"].lower()] = coin_id

        last_update_time = current_time
        print(f"成功更新代币列表，共 {len(coins_data)} 个代币")
        return token_mappings
    except requests.RequestException as e:
        print(f"更新代币列表失败: {e}")
        return token_mappings


def query_gpt(user_input):
    """
    调用 GPT 模型处理用户输入。
    """
    if not API_KEY:
        return "Request error: missing YUNWU_API_KEY environment variable"

    # 确保代币映射是最新的
    update_token_mappings()

    common_tokens = (
        "BTC/Bitcoin -> bitcoin, "
        "ETH/Ethereum -> ethereum, "
        "SOL/Solana -> solana, "
        "XRP/Ripple -> ripple, "
        "BNB -> binancecoin, "
        "DOGE -> dogecoin, "
        "PEPE -> pepe, "
        "SHIB -> shiba-inu"
    )

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a cryptocurrency assistant. "
                    "Your task is to recognize cryptocurrency names or symbols and convert them to their proper IDs. "
                    f"Common examples: {common_tokens}. "
                    "I have access to all cryptocurrencies listed on CoinGecko. "
                    "When the user inquires about a cryptocurrency, respond in this JSON format: "
                    "{'format_price': true, 'token_name': '<TOKEN_ID>'}. "
                    "If you're not completely sure about the token ID, respond with 'Unknown token' "
                    "to avoid providing incorrect information."
                ),
            },
            {"role": "user", "content": user_input},
        ],
    }

    try:
        response = requests.post(
            GPT_API_URL,
            headers=_build_headers(),
            json=data,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        gpt_response = result["choices"][0]["message"]["content"].strip()

        try:
            response_data = json.loads(gpt_response.replace("'", '"'))
            token_id = response_data.get("token_name", "").lower()
            if token_id and valid_token_ids and token_id not in valid_token_ids:
                return "Unknown token"
        except json.JSONDecodeError:
            pass

        return gpt_response
    except requests.RequestException as e:
        return f"Request error: {e}"
    except KeyError:
        return "Unexpected response format from GPT API."


def fetch_crypto_price(token_name, currency="usd"):
    """
    调用 FastAPI 获取加密货币的价格。
    """
    token_name = token_name.lower()
    url = f"{FASTAPI_URL}/price/"

    try:
        print(f"正在请求价格数据: {url}?coin={token_name}&currency={currency}")
        response = requests.get(
            url,
            params={"coin": token_name, "currency": currency},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        price_data = response.json()
        print(f"成功获取价格数据: {price_data}")
        return price_data
    except requests.RequestException as e:
        error_msg = f"FastAPI请求错误: {str(e)}"
        print(error_msg)
        return {"error": error_msg}
    except ValueError as e:
        error_msg = f"解析JSON响应错误: {str(e)}"
        print(error_msg)
        return {"error": error_msg}
