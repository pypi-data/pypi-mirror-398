import requests
import json
from typing import List, Dict, Any

def fetch_products() -> str:
    """
    获取电商产品列表。
    来源: https://fakestoreapi.com/products
    返回: JSON 格式的产品列表字符串，包含 id, title, price, description, category, image, rating 等字段。
    """
    try:
        response = requests.get("https://fakestoreapi.com/products")
        response.raise_for_status()
        
        # 1. response.text 本身就是 API 返回的 JSON 字符串
        # 2. 我们直接返回这个字符串，MCP 协议会把它封装在一个 TextContent 对象中传给大模型
        # 3. 大模型看到这个 JSON 字符串后，会自动解析其结构
        return response.text
        
    except Exception as e:
        # 发生错误时，我们也返回一个 JSON 格式的错误信息，这样更规范
        error_info = {
            "error": True,
            "message": str(e)
        }
        return json.dumps(error_info)
