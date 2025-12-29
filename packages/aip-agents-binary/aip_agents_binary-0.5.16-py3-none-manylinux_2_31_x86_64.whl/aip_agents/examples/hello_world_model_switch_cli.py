"""Hello World Model Switch CLI.

This example demonstrates the enhanced credential system for various LLM providers.

New Auto-Detection Features:
- Dictionary credentials (e.g., AWS Bedrock)
- File path credentials (e.g., Google service account JSON)
- API key strings (e.g., OpenAI, Google API keys)

The system automatically detects credential types - no manual type specification needed!

Setup Environment Variables:
- BEDROCK_ACCESS_KEY_ID: Your AWS access key for Bedrock
- BEDROCK_SECRET_ACCESS_KEY: Your AWS secret key for Bedrock
- GOOGLE_VERTEX_AI_CREDENTIAL_PATH: Path to Google service account JSON file
- DEEPINFRA_API_KEY: API key for DeepInfra models

Authors:
    Putu R Wiguna (putu.r.wiguna@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from aip_agents.agent import LangChainAgent
from aip_agents.schema.agent import AgentConfig

load_dotenv()

# You can adjust these model ids to match your backend's supported models
DEEPINFRA_URL = "https://api.deepinfra.com/v1/openai"
MODEL_IDS = [
    "openai/gpt-4.1",
    "google/gemini-2.5-flash",
    "bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0",  # Amazon Bedrock example
    "google/gemini-2.5-pro",  # Google Gemini with service account file
    "openai-compatible/https://api.deepinfra.com/v1/openai:Qwen/Qwen3-30B-A3B",
    "openai-compatible/https://api.deepinfra.com/v1/openai:deepseek-ai/DeepSeek-V3",
    "openai-compatible/https://api.deepinfra.com/v1/openai:deepseek-ai/DeepSeek-R1-0528",
    # our vllm
    "openai-compatible/https://ai-agent-vllm.obrol.id/v1/:Qwen/Qwen3-32B-AWQ",  # ensure to turn on vllm-server
    "openai-compatible/Qwen/Qwen3-30B-A3B",
    # Azure OpenAI example
    "azure-openai/https://glair-genai-benchmark.openai.azure.com:glair-benchmark-gpt-4o-mini",
]

MODEL_CONFIGS = {
    # Amazon Bedrock - Dictionary credentials (auto-detected)
    "bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0": AgentConfig(
        lm_credentials={
            "access_key_id": os.getenv("BEDROCK_ACCESS_KEY_ID", "your-aws-access-key-id"),
            "secret_access_key": os.getenv("BEDROCK_SECRET_ACCESS_KEY", "your-aws-secret-access-key"),
        },
        lm_hyperparameters={"temperature": 0.7, "maxTokens": 1000},
    ),
    # Google Gemini with service account file - File path (auto-detected)
    "google/gemini-2.5-pro": AgentConfig(
        lm_credentials=os.getenv("GOOGLE_VERTEX_AI_CREDENTIAL_PATH", "/path/to/service-account.json"),
        lm_hyperparameters={"temperature": 0.7},
    ),
    # Legacy configurations using lm_api_key (still supported)
    "openai-compatible/https://api.deepinfra.com/v1/openai:Qwen/Qwen3-30B-A3B": AgentConfig(
        lm_base_url=DEEPINFRA_URL,
        lm_api_key=os.getenv("DEEPINFRA_API_KEY"),  # Legacy field still works
    ),
    "openai-compatible/https://api.deepinfra.com/v1/openai:deepseek-ai/DeepSeek-V3": AgentConfig(
        lm_base_url=DEEPINFRA_URL,
        lm_api_key=os.getenv("DEEPINFRA_API_KEY"),
    ),
    "openai-compatible/https://api.deepinfra.com/v1/openai:deepseek-ai/DeepSeek-R1-0528": AgentConfig(
        lm_base_url=DEEPINFRA_URL,
        lm_api_key=os.getenv("DEEPINFRA_API_KEY"),
    ),
    "openai-compatible/https://ai-agent-vllm.obrol.id/v1/:Qwen/Qwen3-32B-AWQ": AgentConfig(
        lm_base_url="https://ai-agent-vllm.obrol.id/v1/",
        lm_hyperparameters={"temperature": 1.0},
    ),
    "openai-compatible/Qwen/Qwen3-30B-A3B": AgentConfig(
        lm_base_url=DEEPINFRA_URL,
        lm_api_key=os.getenv("DEEPINFRA_API_KEY"),
    ),
    "openai-compatible/Qwen/Qwen3-32B-AWQ": AgentConfig(
        lm_base_url="https://ai-agent-vllm.obrol.id/v1/",
        lm_hyperparameters={"temperature": 1.0},
    ),
    "openai/gpt-4.1": AgentConfig(
        lm_hyperparameters={"temperature": 1.0},
    ),
    "azure-openai/https://glair-genai-benchmark.openai.azure.com:glair-benchmark-gpt-4o-mini": AgentConfig(
        lm_base_url="https://glair-genai-benchmark.openai.azure.com",
    ),
}


def make_agent(model_id):
    """Makes an agent with the given model id.

    Args:
        model_id: The model identifier to use for the agent.

    Returns:
        LangChainAgent: The configured agent instance.
    """
    config = MODEL_CONFIGS.get(model_id)
    agent = LangChainAgent(
        name=f"HelloWorldAgent-{model_id}",
        instruction="You are a helpful assistant.",
        model=model_id,
        config=config,
    )
    return agent


def print_help():
    """Prints available commands and their descriptions."""
    help_text = (
        "\nAvailable commands:\n"
        "  /help    Show this help message\n"
        "  /switch  Switch to another model\n"
        "  /exit    Quit the chat\n"
        "Type anything else to chat with the assistant.\n"
    )
    print(help_text)


def handle_switch_model(current_model):
    """Handles model switching. Returns (new_model, new_agent).

    Args:
        current_model: The currently active model identifier.

    Returns:
        tuple: (new_model, new_agent) where new_model is the selected model ID and new_agent is the configured agent instance.
    """
    print(f"Current model: {current_model}")
    print("Available models:")
    for idx, m in enumerate(MODEL_IDS):
        print(f"  [{idx + 1}] {m}")
    try:
        selection = input("Select model number: ").strip()
        idx = int(selection) - 1
        if idx < 0 or idx >= len(MODEL_IDS):
            print("Invalid selection. No switch performed.")
            return current_model, make_agent(current_model)
        new_model = MODEL_IDS[idx]
    except Exception:
        print("Invalid input. No switch performed.")
        return current_model, make_agent(current_model)
    print(f"Switched to model: {new_model}")
    return new_model, make_agent(new_model)


def main():
    """Runs the Hello World Model Switch CLI."""
    print("Welcome to the Hello World Model Switch CLI!")
    print("🎯 Demonstrating Enhanced Credential Auto-Detection:")
    print("  • AWS Bedrock with dictionary credentials")
    print("  • Google Gemini with API key")
    print("  • Google Gemini with service account file")
    print("  • Legacy lm_api_key support still works!")
    print()
    print(f"Available models: {MODEL_IDS}")
    current_model = MODEL_IDS[0]
    agent = make_agent(current_model)
    print(f"Loaded model: {current_model}")
    print("Type your message, or type /switch to change model, or /exit to quit or /help to show available commands.")

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
        elif user_input.lower() == "/switch":
            current_model, agent = handle_switch_model(current_model)
            continue
        elif user_input == "":
            continue
        # Add user message to history
        messages.append(HumanMessage(content=user_input))
        # Run the agent synchronously with history
        try:
            response = agent.run(query=user_input, messages=messages[:-1])
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
            print(f"Agent ({current_model}): {ai_message.content}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
