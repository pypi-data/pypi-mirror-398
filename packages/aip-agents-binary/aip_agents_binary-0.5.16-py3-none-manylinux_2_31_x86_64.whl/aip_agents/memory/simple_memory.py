"""Simple Memory Module for AIP Agents.

This module provides a basic implementation of the BaseMemory class
that stores messages in a simple list structure.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from aip_agents.memory.base import BaseMemory, ChatMessage


class SimpleMemory(BaseMemory):
    """A simple memory implementation that stores messages in a list."""

    def __init__(self):
        """Initialize the SimpleMemory instance with an empty message list."""
        self.messages: list[ChatMessage] = []

    def add_message(self, message_or_role, content=None) -> None:
        """Add a message to memory.

        Supports two calling patterns for backward compatibility:
        1. add_message(ChatMessage) - Adds a ChatMessage object directly
        2. add_message(role, content) - Creates and adds a ChatMessage with the given role and content

        Args:
            message_or_role: Either a ChatMessage object or a string role (e.g., "user", "assistant").
            content: Optional content string when using the role+content pattern.
                Required when message_or_role is a string role.
        """
        if content is not None:
            # Using the role+content pattern
            self.messages.append(ChatMessage(role=message_or_role, content=content))
        else:
            # Using the ChatMessage object pattern
            self.messages.append(message_or_role)

    def get_messages(self) -> list[ChatMessage]:
        """Get all messages from memory."""
        return self.messages

    def clear(self) -> None:
        """Clear all messages from memory."""
        self.messages = []

    # Uses the default get_memory_variables implementation from BaseMemory
