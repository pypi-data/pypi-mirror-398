from aip_agents.memory.base import BaseMemory as BaseMemory, ChatMessage as ChatMessage

class SimpleMemory(BaseMemory):
    """A simple memory implementation that stores messages in a list."""
    messages: list[ChatMessage]
    def __init__(self) -> None:
        """Initialize the SimpleMemory instance with an empty message list."""
    def add_message(self, message_or_role, content=None) -> None:
        '''Add a message to memory.

        Supports two calling patterns for backward compatibility:
        1. add_message(ChatMessage) - Adds a ChatMessage object directly
        2. add_message(role, content) - Creates and adds a ChatMessage with the given role and content

        Args:
            message_or_role: Either a ChatMessage object or a string role (e.g., "user", "assistant").
            content: Optional content string when using the role+content pattern.
                Required when message_or_role is a string role.
        '''
    def get_messages(self) -> list[ChatMessage]:
        """Get all messages from memory."""
    def clear(self) -> None:
        """Clear all messages from memory."""
