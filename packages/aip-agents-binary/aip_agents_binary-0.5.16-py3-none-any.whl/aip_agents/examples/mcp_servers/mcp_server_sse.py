"""Weather Forecast & Text Tools MCP by SSE with multiple tools."""

from mcp.server.fastmcp import FastMCP

from aip_agents.examples.mcp_servers.common import get_random_quote, word_count
from aip_agents.examples.tools.weather_forecast_tool import get_weather_forecast

if __name__ == "__main__":
    mcp = FastMCP("Weather-Text SSE Server", port=8123)
    mcp.add_tool(get_weather_forecast, name="get_weather_forecast")
    mcp.add_tool(get_random_quote, name="get_random_quote")
    mcp.add_tool(word_count, name="word_count")

    print("Starting SSE MCP Server with 3 tools:")
    print("- get_weather_forecast")
    print("- get_random_quote")
    print("- word_count")

    mcp.run(transport="sse")
