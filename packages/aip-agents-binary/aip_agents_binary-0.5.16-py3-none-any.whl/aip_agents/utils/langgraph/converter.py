"""Bridge utilities for converting between LangChain and LM Invoker formats.

This module provides conversion functions between LangChain's message format
and gllm-inference's Message format, enabling seamless integration
of LM Invoker with LangChain-based agents.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from collections.abc import Sequence

from gllm_inference.schema import LMOutput, Message, ToolResult
from gllm_inference.schema import ToolCall as GllmToolCall
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
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
    converted_messages = []

    # Add system instruction first if provided
    if instruction:
        converted_messages.append(Message.system(instruction))

    for msg in messages:
        if isinstance(msg, SystemMessage):
            # Skip if we already added instruction, or append if different
            if not instruction or msg.content != instruction:
                converted_messages.append(Message.system(msg.content))
        elif isinstance(msg, HumanMessage):
            converted_messages.append(Message.user(msg.content))
        elif isinstance(msg, AIMessage):
            if msg.tool_calls:
                # Convert LangChain tool calls to gllm ToolCall objects
                tool_calls = [convert_langchain_tool_call_to_gllm_tool_call(tc) for tc in msg.tool_calls]
                converted_messages.append(Message.assistant(tool_calls))
            else:
                converted_messages.append(Message.assistant(msg.content))
        elif isinstance(msg, ToolMessage):
            # Convert ToolMessage to ToolResult
            tool_result = ToolResult(id=msg.tool_call_id, output=msg.content)
            converted_messages.append(Message.user([tool_result]))

    return converted_messages


def convert_lm_output_to_langchain_message(response: LMOutput | str) -> AIMessage:
    """Convert LM Invoker output to LangChain AIMessage.

    This function transforms the output from LM Invoker back into LangChain's
    AIMessage format, handling both text responses and tool calls.

    Args:
        response: The response from LM Invoker (MultimodalOutput).

    Returns:
        AIMessage containing the converted response.
    """
    if not isinstance(response, LMOutput):
        # when output_analytics lm_invoker is false
        return AIMessage(
            content=str(response),
            response_metadata={
                "finish_reason": "stop",
            },
        )

    tool_calls = []
    if response.tool_calls:
        tool_calls = [convert_gllm_tool_call_to_langchain_tool_call(tc) for tc in response.tool_calls]

    usage_metadata = None
    if response.token_usage:
        usage_metadata = {
            "input_tokens": response.token_usage.input_tokens,
            "output_tokens": response.token_usage.output_tokens,
            "total_tokens": response.token_usage.input_tokens + response.token_usage.output_tokens,
        }

    # if add finish reason stop fo non-tool call ai messages
    response_metadata = {}
    if not tool_calls:
        response_metadata["finish_reason"] = "stop"

    return AIMessage(
        content=str(response.response),
        tool_calls=tool_calls,
        usage_metadata=usage_metadata,
        response_metadata=response_metadata,
    )


def convert_langchain_tool_call_to_gllm_tool_call(lc_tool_call: LangChainToolCall) -> GllmToolCall:
    """Convert LangChain tool call to gllm ToolCall.

    Args:
        lc_tool_call: LangChain ToolCall (TypedDict).

    Returns:
        GllmToolCall object for gllm-inference.
    """
    return GllmToolCall(id=lc_tool_call["id"], name=lc_tool_call["name"], args=lc_tool_call["args"])


def convert_gllm_tool_call_to_langchain_tool_call(gllm_tool_call: GllmToolCall) -> LangChainToolCall:
    """Convert gllm ToolCall to LangChain ToolCall format.

    Args:
        gllm_tool_call: GllmToolCall object from gllm-inference.

    Returns:
        LangChain ToolCall (TypedDict) with proper type annotation.
    """
    return LangChainToolCall(id=gllm_tool_call.id, name=gllm_tool_call.name, args=gllm_tool_call.args)
