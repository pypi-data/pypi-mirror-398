from dataclasses import dataclass

@dataclass
class ToolApprovalConfig:
    """Configuration for HITL approval behavior attached to a tool.

    Supplying this configuration marks the tool as requiring approval. Only the
    timeout is configurable; timeouts always result in a safe skip.

    Attributes:
        timeout_seconds: Defaults to 300; must be >0.
    """
    timeout_seconds: int = ...
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
