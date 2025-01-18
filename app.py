import json  # 确保已导入
from crypto_utils import query_gpt, fetch_crypto_price

if __name__ == "__main__":
    while True:
        user_input = input("请输入你的问题 (输入 'exit' 退出): ")
        if user_input.lower() == "exit":
            break

        # 调用 GPT 模型
        gpt_result = query_gpt(user_input)
        # print("GPT 响应:", gpt_result)  # 注释掉这行，不显示原始响应

        # 解析 GPT 输出
        if "Unknown token" in gpt_result:
            print("无法识别的币种，请检查输入。")
        else:
            try:
                # 处理 GPT 响应中的引号问题
                gpt_result = gpt_result.strip("'")  # 移除可能的外部单引号
                gpt_result = gpt_result.replace("True", "true").replace("False", "false")
                
                # 使用 json.loads() 解析 GPT 返回的 JSON 字符串
                gpt_data = json.loads(
                    gpt_result.replace("'", '"')  # 替换单引号为双引号
                )

                token_name = gpt_data.get("token_name")
                if token_name:
                    # 将币种名称转换为小写字母，以确保与 FastAPI 兼容
                    token_name = token_name.lower()
                    print(f"\n正在查询币种: {token_name}")
                    
                    # 调用 FastAPI 获取价格
                    price_result = fetch_crypto_price(token_name)
                    
                    if "error" in price_result:
                        print(f"获取价格失败: {price_result['error']}")
                    else:
                        print("\n价格信息:")
                        print(f"币种: {price_result['coin']}")
                        print(f"价格: {price_result['price']} {price_result['currency'].upper()}")
                else:
                    print("GPT 响应中未包含有效的币种名称。")
            except json.JSONDecodeError as e:
                print("解析 GPT 响应时出错: 无法解析为 JSON:", e)
            except Exception as e:
                print("解析 GPT 响应时发生未知错误:", e)
