"""Time MCP Tool STDIO."""

from mcp.server.fastmcp import FastMCP

from aip_agents.examples.mcp_servers.common import get_current_time as time_tool

if __name__ == "__main__":
    mcp = FastMCP("Time")
    mcp.add_tool(time_tool, name="time")
    mcp.run(transport="stdio")
