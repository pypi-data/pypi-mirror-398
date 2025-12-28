"""
Tool registration module.
Import and register all tool functions here.
"""

from mcp.server.fastmcp import FastMCP
from datsluo_sj_mcp.tools.patent_search import search_cn_patent, search_wipo_patent

def register_tools(mcp: FastMCP) -> None:
    """
    Register all tools to the MCP server instance.
    
    Args:
        mcp: The FastMCP server instance.
    """
    
    # Register Patent Search Tools
    # FastMCP automatically parses the function signature and docstrings
    mcp.tool()(search_cn_patent)
    mcp.tool()(search_wipo_patent)
    
    # Example placeholder tool (can be removed later)
    @mcp.tool()
    def add(a: int, b: int) -> int:
        """
        Add two numbers. A simple connectivity test tool.
        """
        return a + b
