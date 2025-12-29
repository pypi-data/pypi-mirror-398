"""Configuration for MCP servers."""

mcp_config_sse = {
    "playwright_tools": {
        "url": "http://localhost:8931/sse",
        "transport": "sse",
    }
}


mcp_config_stdio = {
    "weather_tools": {
        "command": "python",
        "args": ["aip_agents/examples/mcp_servers/mcp_server_stdio.py"],
        "transport": "stdio",
    }
}

mcp_config_http = {
    "playwright_tools": {
        "url": "http://localhost:8931/mcp",
        "transport": "http",
    }
}


mcp_multi_server = {
    "sse_secretmsg": {
        "url": "http://localhost:8123/sse",
        "transport": "sse",
    },
    "stdio_time": {
        "command": "python",
        "args": ["aip_agents/examples/mcp_servers/mcp_time.py"],
        "transport": "stdio",
    },
    "http_playwright_tools": {
        "url": "http://localhost:8931/mcp",
        "transport": "http",
    },
}

mcp_tool_whitelisting_demo = {
    # STDIO server - allow only get_current_time (whitelist approach)
    "stdio_time": {
        "command": "python",
        "args": ["aip_agents/examples/mcp_servers/mcp_server_stdio.py"],
        "transport": "stdio",
        "allowed_tools": ["get_current_time"],
    },
    # SSE server - allow only get_random_quote (whitelist approach)
    "sse_quotes": {
        "url": "http://localhost:8123/sse",
        "transport": "sse",
        "allowed_tools": ["get_random_quote"],
    },
    # HTTP server - allow only get_random_fact (whitelist approach)
    "http_facts": {
        "url": "http://localhost:8931/mcp",
        "transport": "streamable-http",
        "allowed_tools": ["get_random_fact"],
    },
}
