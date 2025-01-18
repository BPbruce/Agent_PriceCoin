import requests
import time

# 配置
GPT_API_URL = "https://yunwu.ai/v1/chat/completions"
FASTAPI_URL = "http://127.0.0.1:8000"  # 本地 FastAPI 地址
API_KEY = "sk-XFywchTEhR8sVTQd65399eA6F1Af49F8831e5338Cb1c4796"
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/list"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 缓存代币映射
token_mappings = {}
last_update_time = 0
UPDATE_INTERVAL = 3600  # 每小时更新一次

def update_token_mappings():
    """
    从 CoinGecko 获取最新的代币列表并更新映射
    """
    global token_mappings, last_update_time
    
    current_time = time.time()
    if current_time - last_update_time < UPDATE_INTERVAL and token_mappings:
        return token_mappings
    
    try:
        print("正在从 CoinGecko 更新代币列表...")
        response = requests.get(COINGECKO_API_URL)
        response.raise_for_status()
        coins_data = response.json()
        
        # 清空旧的映射
        token_mappings.clear()
        
        # 为每个代币创建映射
        for coin in coins_data:
            # 添加 symbol -> id 映射
            token_mappings[coin['symbol'].upper()] = coin['id']
            # 添加 name -> id 映射
            token_mappings[coin['name'].lower()] = coin['id']
        
        last_update_time = current_time
        print(f"成功更新代币列表，共 {len(coins_data)} 个代币")
        return token_mappings
    except Exception as e:
        print(f"更新代币列表失败: {e}")
        return token_mappings

def query_gpt(user_input):
    """
    调用 GPT 模型处理用户输入。
    """
    # 确保代币映射是最新的
    mappings = update_token_mappings()
    
    # 生成映射说明
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
                )
            },
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post(GPT_API_URL, headers=HEADERS, json=data)
        response.raise_for_status()
        result = response.json()
        gpt_response = result['choices'][0]['message']['content'].strip()
        
        # 验证 GPT 返回的代币 ID
        try:
            import json
            response_data = json.loads(gpt_response.replace("'", '"'))
            if 'token_name' in response_data:
                token_id = response_data['token_name'].lower()
                # 验证代币 ID 是否在我们的映射中
                if token_id not in set(mappings.values()):
                    return "Unknown token"
        except:
            pass
            
        return gpt_response
    except requests.exceptions.RequestException as e:
        return f"Request error: {e}"
    except KeyError:
        return "Unexpected response format from GPT API."

def fetch_crypto_price(token_name, currency="usd"):
    """
    调用 FastAPI 获取加密货币的价格。
    """
    # 确保传递给 FastAPI 的币种名称是小写的
    token_name = token_name.lower()
    url = f"{FASTAPI_URL}/price/"
    
    try:
        print(f"正在请求价格数据: {url}?coin={token_name}&currency={currency}")
        response = requests.get(url, params={"coin": token_name, "currency": currency})
        response.raise_for_status()
        price_data = response.json()
        print(f"成功获取价格数据: {price_data}")
        return price_data
    except requests.exceptions.RequestException as e:
        error_msg = f"FastAPI请求错误: {str(e)}"
        print(error_msg)
        return {"error": error_msg}
    except ValueError as e:
        error_msg = f"解析JSON响应错误: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

