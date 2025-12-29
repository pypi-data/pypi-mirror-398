"""Weather Forecast & Time Tools MCP by STDIO with multiple tools."""

from mcp.server.fastmcp import FastMCP

from aip_agents.examples.mcp_servers.common import generate_uuid, get_current_time
from aip_agents.examples.tools.weather_forecast_tool import get_weather_forecast

if __name__ == "__main__":
    mcp = FastMCP("Weather-Time STDIO Server")
    mcp.add_tool(get_weather_forecast, name="get_weather_forecast")
    mcp.add_tool(get_current_time, name="get_current_time")
    mcp.add_tool(generate_uuid, name="generate_uuid")

    print("Starting STDIO MCP Server with 3 tools:")
    print("- get_weather_forecast")
    print("- get_current_time")
    print("- generate_uuid")

    mcp.run(transport="stdio")
