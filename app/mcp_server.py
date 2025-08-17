# Minimal MCP server exposing a simple 'upper' tool.
# You can run it with: python -m app.mcp_server
# Docs: https://github.com/modelcontextprotocol/python-sdk
from mcp.server.fastmcp import MCPServer, tool
import asyncio

server = MCPServer("softvence-ai-task-mcp")

@tool()
def upper(text: str) -> str:
    """Return the text in uppercase (demo tool)."""
    return text.upper()

async def main():
    await server.run_stdio()  # stdio transport

if __name__ == "__main__":
    asyncio.run(main())
