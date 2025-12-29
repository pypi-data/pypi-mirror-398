from collections.abc import Sequence
from gllm_inference.schema import LMOutput, Message, ToolCall as GllmToolCall
from langchain_core.messages import AIMessage, BaseMessage as BaseMessage
from langchain_core.messages.tool import ToolCall as LangChainToolCall

def convert_langchain_messages_to_gllm_messages(messages: Sequence[BaseMessage], instruction: str) -> list[Message]:
    """Convert LangChain messages to gllm-inference Message format.

    This function transforms a sequence of LangChain messages into the Message
    format expected by LM Invoker. It handles system messages, human messages, AI messages
    with tool calls, and tool result messages.

    Args:
        messages: Sequence of LangChain BaseMessage objects to convert.
        instruction: System instruction to prepend if not already present in messages.

    Returns:
        List of Message objects containing the converted message sequence.
    """
def convert_lm_output_to_langchain_message(response: LMOutput | str) -> AIMessage:
    """Convert LM Invoker output to LangChain AIMessage.

    This function transforms the output from LM Invoker back into LangChain's
    AIMessage format, handling both text responses and tool calls.

    Args:
        response: The response from LM Invoker (MultimodalOutput).

    Returns:
        AIMessage containing the converted response.
    """
def convert_langchain_tool_call_to_gllm_tool_call(lc_tool_call: LangChainToolCall) -> GllmToolCall:
    """Convert LangChain tool call to gllm ToolCall.

    Args:
        lc_tool_call: LangChain ToolCall (TypedDict).

    Returns:
        GllmToolCall object for gllm-inference.
    """
def convert_gllm_tool_call_to_langchain_tool_call(gllm_tool_call: GllmToolCall) -> LangChainToolCall:
    """Convert gllm ToolCall to LangChain ToolCall format.

    Args:
        gllm_tool_call: GllmToolCall object from gllm-inference.

    Returns:
        LangChain ToolCall (TypedDict) with proper type annotation.
    """
