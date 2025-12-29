from _typeshed import Incomplete
from aip_agents.utils.logger import LoggerManager as LoggerManager
from aip_agents.utils.pii.uuid_deanonymizer_mapping import UUIDDeanonymizerMapping as UUIDDeanonymizerMapping
from enum import Enum
from gllm_privacy.pii_detector import TextAnalyzer, TextAnonymizer
from typing import Any

TextAnalyzer = Any
TextAnonymizer = Any
GDPLabsNerApiRemoteRecognizer = Any

class _Operation(str, Enum):
    ANONYMIZE: str
    DEANONYMIZE: str

logger: Incomplete
NER_API_URL_ENV_VAR: str
NER_API_KEY_ENV_VAR: str
NER_API_TIMEOUT: int
EXCLUDED_ENTITIES: Incomplete
DEFAULT_SUPPORTED_ENTITIES: Incomplete

class ToolPIIHandler:
    """Handles PII masking/demasking for tool calling.

    Tag replacement based on runner-provided mappings always works. Optional
    NER-powered masking/de-masking is only enabled when NER_API_URL and
    NER_API_KEY environment variables are set.

    Attributes:
        flat_pii_mapping: Flat mapping from runner service (tag → value)
        text_analyzer: GLLM Privacy TextAnalyzer instance
        text_anonymizer: GLLM Privacy TextAnonymizer instance
        enable_ner: Whether NER is enabled
    """
    flat_pii_mapping: dict[str, str]
    enable_ner: bool
    text_analyzer: TextAnalyzer | None
    text_anonymizer: TextAnonymizer | None
    def __init__(self, pii_mapping: dict[str, str] | None = None, ner_api_url: str | None = None, ner_api_key: str | None = None) -> None:
        """Initialize PII handler (private - use create_if_enabled() instead).

        Initializes GLLM Privacy components (TextAnalyzer, TextAnonymizer) if NER credentials
        are provided. Creates dual recognizers for Indonesian and English languages.
        Pre-loads any existing PII mappings into the anonymizer's internal state.

        Args:
            pii_mapping: Existing PII mapping from runner service (flat format: tag -> value)
            ner_api_url: NER API endpoint URL
            ner_api_key: NER API authentication key
        """
    @classmethod
    def create_if_enabled(cls, pii_mapping: dict[str, str] | None = None) -> ToolPIIHandler | None:
        """Create ToolPIIHandler when mappings or NER configuration exist.

        Args:
            pii_mapping: Existing PII mapping from runner service

        Returns:
            ToolPIIHandler instance when mapping or NER config is available, None otherwise
        """
    @classmethod
    def create_mapping_only(cls, pii_mapping: dict[str, str] | None = None) -> ToolPIIHandler | None:
        """Create ToolPIIHandler in mapping-only mode (no NER).

        Args:
            pii_mapping: Existing PII mapping from runner service

        Returns:
            ToolPIIHandler instance when mapping exists, None otherwise
        """
    def deanonymize_tool_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Replace PII tags in tool arguments with real values.

        Recursively processes dictionaries, lists, and strings to replace all PII tags
        (e.g., '<EMAIL_1>') with their corresponding real values from flat_pii_mapping.

        Args:
            args: Tool arguments that may contain PII tags

        Returns:
            Arguments with tags replaced by real values
        """
    def anonymize_tool_output(self, output: Any) -> tuple[Any, dict[str, str]]:
        """Mask PII values in tool output.

        Handles string and dictionary outputs. For strings, uses two-phase anonymization:
        first masks known PII, then detects new PII via NER. For dictionaries, recursively
        processes all string values. Returns updated mapping with any newly discovered PII.

        Args:
            output: Tool output that may contain PII values (string, dict, or other)

        Returns:
            Tuple of (anonymized_output, updated_flat_pii_mapping)
        """
