import json

from crypto_utils import fetch_crypto_price, query_gpt


def parse_gpt_response(gpt_result: str):
    """解析 GPT 返回的 token_name。"""
    normalized = gpt_result.strip("'").replace("True", "true").replace("False", "false")
    data = json.loads(normalized.replace("'", '"'))
    return data.get("token_name")


if __name__ == "__main__":
    while True:
        user_input = input("请输入你的问题 (输入 'exit' 退出): ")
        if user_input.lower() == "exit":
            break

        gpt_result = query_gpt(user_input)

        if "Unknown token" in gpt_result:
            print("无法识别的币种，请检查输入。")
            continue

        try:
            token_name = parse_gpt_response(gpt_result)
            if not token_name:
                print("GPT 响应中未包含有效的币种名称。")
                continue

            token_name = token_name.lower()
            print(f"\n正在查询币种: {token_name}")
            price_result = fetch_crypto_price(token_name)

            if "error" in price_result:
                print(f"获取价格失败: {price_result['error']}")
            else:
                print("\n价格信息:")
                print(f"币种: {price_result['coin']}")
                print(f"价格: {price_result['price']} {price_result['currency'].upper()}")
        except json.JSONDecodeError as e:
            print("解析 GPT 响应时出错: 无法解析为 JSON:", e)
        except Exception as e:
            print("解析 GPT 响应时发生未知错误:", e)
