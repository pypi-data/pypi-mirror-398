"""Weather Forecast & Trivia Tools MCP by Streamable HTTP with multiple tools."""

from mcp.server.fastmcp import FastMCP

from aip_agents.examples.mcp_servers.common import convert_to_base64, get_random_fact
from aip_agents.examples.tools.weather_forecast_tool import get_weather_forecast

if __name__ == "__main__":
    mcp = FastMCP("Weather-Trivia HTTP Server", port=8931)
    mcp.add_tool(get_weather_forecast, name="get_weather_forecast")
    mcp.add_tool(get_random_fact, name="get_random_fact")
    mcp.add_tool(convert_to_base64, name="convert_to_base64")

    print("Starting HTTP MCP Server with 3 tools:")
    print("- get_weather_forecast")
    print("- get_random_fact")
    print("- convert_to_base64")

    mcp.run(transport="streamable-http")
