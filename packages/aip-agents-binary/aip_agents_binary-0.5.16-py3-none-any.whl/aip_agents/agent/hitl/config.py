"""HITL configuration dataclasses.

This module defines configuration structures for Human-in-the-Loop approval settings.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from dataclasses import dataclass


@dataclass
class ToolApprovalConfig:
    """Configuration for HITL approval behavior attached to a tool.

    Supplying this configuration marks the tool as requiring approval. Only the
    timeout is configurable; timeouts always result in a safe skip.

    Attributes:
        timeout_seconds: Defaults to 300; must be >0.
    """

    timeout_seconds: int = 300

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
