# Crypto Price Query System

一个基于 GPT 和 CoinGecko 的加密货币价格查询系统。

## 功能特点

- 支持自然语言查询加密货币价格
- 实时获取 CoinGecko 价格数据
- 支持多种加密货币查询

## 安装步骤

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 设置环境变量：
   - `YUNWU_API_KEY`：GPT 接口密钥（必填）
   - `FASTAPI_URL`：价格服务地址（可选，默认 `http://127.0.0.1:8000`）
4. 启动 API 服务：`uvicorn app:app --reload`
5. 启动命令行客户端：`python main.py`
