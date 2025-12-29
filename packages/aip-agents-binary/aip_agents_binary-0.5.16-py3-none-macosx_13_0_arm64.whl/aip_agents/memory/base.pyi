from abc import ABC, abstractmethod
from aip_agents.types import ChatMessage as ChatMessage
from collections.abc import Sequence
from typing import Any

class BaseMemory(ABC):
    """Base class for agent memory.

    This concrete base class provides a default structure. Subclasses
    can inherit from this class to implement specific memory management
    behaviors.
    """
    @classmethod
    def validate_env(cls) -> None:
        """Validate environment prerequisites for a memory backend.

        This hook allows memory implementations to fail fast when required
        environment variables or credentials are missing. Default is a no-op.
        """
    @abstractmethod
    def get_messages(self) -> list[ChatMessage]:
        """Retrieve a list of messages.

        Returns:
            List[ChatMessage]: A list of messages in a generic format.
        """
    @abstractmethod
    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the memory.

        Adds a single ChatMessage to the memory storage. The exact implementation
        depends on the specific memory backend.

        Args:
            message: The ChatMessage object to add to memory. The message should
                contain role and content information.
        """
    def add_messages(self, messages: Sequence[ChatMessage]) -> None:
        """Add multiple messages to the memory.

        Args:
            messages: A sequence of ChatMessage objects to add.
        """
    @abstractmethod
    def clear(self) -> None:
        """Clears the memory or resets the state of the agent.

        This method must be implemented to define the specific behavior
        for clearing or resetting the memory of the agent.
        """
    def get_memory_variables(self) -> dict[str, Any]:
        """Retrieve memory variables.

        This method returns a dictionary containing memory-related variables.
        The default implementation returns a dictionary with chat_history.

        Returns:
            Dict[str, Any]: A dictionary where keys are variable names and values
            are the corresponding memory-related data.
        """
