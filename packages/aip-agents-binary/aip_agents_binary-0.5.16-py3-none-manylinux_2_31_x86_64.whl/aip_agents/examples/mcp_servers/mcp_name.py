"""Random Name Generator MCP Tool by SSE."""

from mcp.server.fastmcp import FastMCP

from aip_agents.examples.mcp_servers.common import get_random_item_from_list

name_list = [
    "Pedri",
    "Joan Garcia",
    "De Jong",
    "Curbasi",
    "Yamal",
    "Kounde",
    "Balde",
    "Raphina",
    "Fermin Lopez",
    "Gavi",
]


def random_name_generator() -> str:
    """Generate random name."""
    return get_random_item_from_list(name_list)


if __name__ == "__main__":
    mcp = FastMCP("Random Name Generator", port=8123)
    mcp.add_tool(random_name_generator, name="random_name_generator")
    mcp.run(transport="sse")
