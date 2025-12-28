"""
Patent search tools module.
Provides tools for searching patents from various sources (CNIPA, WIPO, etc.).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context

# --- Data Models (Pydantic) ---
# Use Pydantic to ensure strict typing and automatic documentation for the LLM.

class PatentResult(BaseModel):
    """Structure for a single patent search result."""
    title: str = Field(..., description="The title of the patent")
    patent_number: str = Field(..., description="The patent publication number (e.g., CN123456A)")
    applicant: str = Field(..., description="The person or company applying for the patent")
    abstract: str = Field(..., description="A brief summary of the patent content")
    publication_date: str = Field(..., description="Date when the patent was published (YYYY-MM-DD)")

# --- Mock Data (Simulation) ---
# Since we don't have real API keys yet, we simulate the API response.
# This ensures the logic flow is correct before connecting to real external APIs.

MOCK_DB = {
    "AI": [
        {
            "title": "一种基于大模型的专利自动分类方法",
            "patent_number": "CN117890123A",
            "applicant": "未来科技技术有限公司",
            "abstract": "本发明公开了一种利用大型语言模型对专利文本进行语义分析并自动归类的技术方案...",
            "publication_date": "2024-01-15"
        },
        {
            "title": "Artificial Intelligence driven patent landscape analysis",
            "patent_number": "US20240012345A1",
            "applicant": "Global Tech Corp",
            "abstract": "System and method for analyzing patent landscapes using deep learning models...",
            "publication_date": "2023-11-20"
        }
    ],
    "5G": [
        {
            "title": "5G通信网络中的大规模MIMO天线阵列",
            "patent_number": "CN112233445B",
            "applicant": "通信巨头股份有限公司",
            "abstract": "一种用于增强5G基站信号覆盖范围的大规模多输入多输出天线设计...",
            "publication_date": "2022-05-10"
        }
    ]
}

# --- Tool Logic ---

def search_cn_patent(keyword: str) -> str:
    """
    Search for Chinese patents (CNIPA) by keyword.
    
    Use this tool when the user asks for patents in China or explicitly mentions CNIPA.
    
    Args:
        keyword: The search query (e.g., "artificial intelligence", "battery thermal management").
    """
    # In a real scenario, we would use `requests.get()` to call the CNIPA/commercial API here.
    # Response = requests.get("https://api.example.com/cn/search", params={"q": keyword})
    
    print(f"[DEBUG] Searching CN patents for: {keyword}")
    
    # Simple mock search logic
    results = []
    for key, patents in MOCK_DB.items():
        if key.lower() in keyword.lower():
            # Filter only CN patents for this specific tool
            cn_patents = [p for p in patents if p["patent_number"].startswith("CN")]
            results.extend(cn_patents)
    
    if not results:
        return f"No Chinese patents found for keyword: {keyword}"
    
    # Format results as a readable string (or JSON) for the LLM
    # Using Pydantic to serialize ensures consistent output format
    formatted_results = [PatentResult(**r).model_dump_json() for r in results]
    return f"Found {len(results)} CN patents:\n" + "\n".join(formatted_results)

def search_wipo_patent(keyword: str) -> str:
    """
    Search for international patents (WIPO/PCT) by keyword.
    
    Use this tool when the user asks for global, international, or PCT patents.
    
    Args:
        keyword: The search query (e.g., "6G communication", "solid state battery").
    """
    print(f"[DEBUG] Searching WIPO patents for: {keyword}")
    
    results = []
    for key, patents in MOCK_DB.items():
        if key.lower() in keyword.lower():
            # Filter non-CN patents (assuming they are international/US for this mock)
            intl_patents = [p for p in patents if not p["patent_number"].startswith("CN")]
            results.extend(intl_patents)
            
    if not results:
        return f"No WIPO/International patents found for keyword: {keyword}"
        
    formatted_results = [PatentResult(**r).model_dump_json() for r in results]
    return f"Found {len(results)} WIPO patents:\n" + "\n".join(formatted_results)
