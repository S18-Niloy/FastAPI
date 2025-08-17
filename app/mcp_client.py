# Minimal MCP client that can call the 'upper' tool of our local server.
# In production, you'd connect to any MCP server by its transport.
# Docs: https://modelcontextprotocol.io/quickstart/client
import asyncio
from mcp import StdioServerParameters
from mcp.client.session import ClientSession
from mcp.client.sse import SSEClientTransport  # not used here, but available
from mcp.client.stdio import stdio_client

async def call_upper(text: str) -> str:
    params = StdioServerParameters(command=["python","-m","app.mcp_server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            tools = await session.list_tools()
            if not any(t.name == "upper" for t in tools.tools):
                raise RuntimeError("upper tool not available")
            result = await session.call_tool("upper", arguments={"text": text})
            # result.content is a list of objects with 'type' and 'text' fields
            chunks = [c.text for c in result.content if getattr(c, "text", None)]
            return "\n".join(chunks) if chunks else ""

if __name__ == "__main__":
    print(asyncio.run(call_upper("hello mcp")))
