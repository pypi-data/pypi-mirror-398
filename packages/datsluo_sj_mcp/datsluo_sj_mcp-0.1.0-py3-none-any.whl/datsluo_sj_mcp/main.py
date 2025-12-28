"""
FastMCP Server Configuration and Entry Point.
"""

from mcp.server.fastmcp import FastMCP
from datsluo_sj_mcp.tools import register_tools

# Initialize the MCP server
# dependencies parameter is managed by uv/pyproject.toml, so we can leave it empty or minimal
mcp = FastMCP(
    "Test MCP Service"
)

# Register all tools
register_tools(mcp)

def main() -> None:
    """
    Main entry point for the MCP server.
    
    This function starts the FastMCP server, which defaults to stdio transport.
    Stdio is the standard transport for local testing and Aliyun Bailian script deployment.
    """
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
