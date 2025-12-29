"""Interactive example showing LangChain agent with MCP tools integration using Streamable HTTP transport.

This script provides an interactive CLI interface with chat history functionality,
similar to hello_world_model_switch_cli.py, but with MCP tools via HTTP transport.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio
import os

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from aip_agents.agent import LangChainAgent
from aip_agents.utils.env_loader import load_local_env

load_local_env()


def print_help():
    """Prints available commands and their descriptions."""
    help_text = (
        "\nAvailable commands:\n"
        "  /help    Show this help message\n"
        "  /exit    Quit the chat\n"
        "Type anything else to chat with the assistant.\n"
    )
    print(help_text)


def build_mcp_config_from_env() -> dict:
    """Construct MCP configuration from environment variables.

    Returns:
        dict: MCP configuration dictionary.

    Raises:
        RuntimeError: If required environment variables are missing.
    """
    url = "https://huggingface.co/mcp"
    token = os.getenv("TEST_HF_TOKEN")

    missing = [
        name
        for name, value in {
            "TEST_HF_TOKEN": token,
        }.items()
        if not value
    ]

    if missing:
        missing_vars = ", ".join(missing)
        raise RuntimeError(
            "Missing required environment variables for MCP configuration: "
            f"{missing_vars}. Please set them before running the example."
        )

    return {
        "mcp_server": {
            "url": url,
            "transport": "http",
            "headers": {
                "Authorization": f"Bearer {token}",
            },
        }
    }


async def main():
    """Runs the interactive LangChainAgent with MCP tools via Streamable HTTP transport."""
    print("Welcome to the Interactive LangChain MCP HTTP Example!")
    print("🎯 Demonstrating MCP tools integration with HTTP transport:")
    print("  • Web browsing capabilities via Playwright tools")
    print()
    print("Type your message, or type /help to show available commands, or /exit to quit.")

    # Initialize the agent with MCP tools
    langchain_agent = LangChainAgent(
        name="interactive_langchain_mcp_example",
        instruction=("You are a helpful assistant."),
        # Using a basic model for the example - you can adjust this as needed
        model="openai/gpt-4.1",  # Changed to a string identifier for consistency
    )
    mcp_config = build_mcp_config_from_env()
    langchain_agent.add_mcp_server(mcp_config)

    # Conversation history as LangChain message objects
    messages = [SystemMessage(content="You are a helpful assistant.")]

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "/help":
            print_help()
            continue
        if user_input.lower() == "/exit":
            print("Goodbye!")
            break
        elif user_input == "":
            continue

        # Add user message to history
        messages.append(HumanMessage(content=user_input))

        # Run the agent with history
        try:
            # Pass the conversation history to the agent
            response = await langchain_agent.arun(query=user_input, messages=messages[:-1])

            # Extract AI message (should be last in response state)
            output = response.get("output")
            ai_message = None

            # Try to find the returned messages in the response (standard pattern)
            if "messages" in response and response["messages"]:
                # Use the last message as the AI reply
                ai_message = response["messages"][-1]
            elif output:
                ai_message = AIMessage(content=output)
            else:
                ai_message = AIMessage(content=str(response))

            messages.append(ai_message)
            print(f"Agent: {ai_message.content}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
