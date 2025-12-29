"""PII handler for masking/demasking at the tool calling level.

This module provides the ToolPIIHandler class for handling PII operations
during tool execution in LangGraph agents. Tag replacement works with the
mapping supplied by the runner, while advanced NER-powered detection is only
enabled when NER_API_URL and NER_API_KEY environment variables are set.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)

References:
    1. https://gdplabs.gitbook.io/sdk/tutorials/security-and-privacy/pii-masking#anonymizer-with-ner
"""

import os
from enum import Enum
from typing import Any

try:
    from gllm_privacy.pii_detector import TextAnalyzer, TextAnonymizer
    from gllm_privacy.pii_detector.anonymizer import Operation
    from gllm_privacy.pii_detector.constants import GLLM_PRIVACY_ENTITIES, Entities
    from gllm_privacy.pii_detector.recognizer.gdplabs_ner_api_remote_recognizer import (
        GDPLabsNerApiRemoteRecognizer,
    )

    _HAS_GLLM_PRIVACY = True
except ImportError:  # pragma: no cover
    TextAnalyzer = Any  # type: ignore[assignment]
    TextAnonymizer = Any  # type: ignore[assignment]
    GDPLabsNerApiRemoteRecognizer = Any  # type: ignore[assignment]

    class _Operation(str, Enum):
        ANONYMIZE = "ANONYMIZE"
        DEANONYMIZE = "DEANONYMIZE"

    Operation = _Operation

    GLLM_PRIVACY_ENTITIES = []  # type: ignore[assignment]
    Entities = None  # type: ignore[assignment]
    _HAS_GLLM_PRIVACY = False

from aip_agents.utils.logger import LoggerManager
from aip_agents.utils.pii.uuid_deanonymizer_mapping import UUIDDeanonymizerMapping

logger = LoggerManager().get_logger(__name__)

NER_API_URL_ENV_VAR = "NER_API_URL"
NER_API_KEY_ENV_VAR = "NER_API_KEY"
NER_API_TIMEOUT = 10
if _HAS_GLLM_PRIVACY:
    EXCLUDED_ENTITIES = [Entities.URL.value]
    DEFAULT_SUPPORTED_ENTITIES = [entity for entity in GLLM_PRIVACY_ENTITIES if entity not in EXCLUDED_ENTITIES]
else:
    EXCLUDED_ENTITIES = []
    DEFAULT_SUPPORTED_ENTITIES = []


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

    def __init__(
        self,
        pii_mapping: dict[str, str] | None = None,
        ner_api_url: str | None = None,
        ner_api_key: str | None = None,
    ) -> None:
        """Initialize PII handler (private - use create_if_enabled() instead).

        Initializes GLLM Privacy components (TextAnalyzer, TextAnonymizer) if NER credentials
        are provided. Creates dual recognizers for Indonesian and English languages.
        Pre-loads any existing PII mappings into the anonymizer's internal state.

        Args:
            pii_mapping: Existing PII mapping from runner service (flat format: tag -> value)
            ner_api_url: NER API endpoint URL
            ner_api_key: NER API authentication key
        """
        self.flat_pii_mapping: dict[str, str] = pii_mapping or {}
        self.enable_ner: bool = bool(ner_api_url and ner_api_key)
        self.text_analyzer: TextAnalyzer | None = None
        self.text_anonymizer: TextAnonymizer | None = None

        if self.enable_ner and not _HAS_GLLM_PRIVACY:
            logger.warning(
                "NER is configured (NER_API_URL/NER_API_KEY present) but optional dependency 'gllm-privacy' "
                "is not installed. Continuing with NER disabled."
            )
            self.enable_ner = False

        if self.enable_ner:
            try:
                headers = {"X-Api-Key": ner_api_key}

                id_recognizer = GDPLabsNerApiRemoteRecognizer(
                    api_url=ner_api_url,
                    supported_language="id",
                    api_headers=headers,
                    api_timeout=NER_API_TIMEOUT,
                )
                en_recognizer = GDPLabsNerApiRemoteRecognizer(
                    api_url=ner_api_url,
                    supported_language="en",
                    api_headers=headers,
                    api_timeout=NER_API_TIMEOUT,
                )

                self.text_analyzer = TextAnalyzer(additional_recognizers=[id_recognizer, en_recognizer])

                # Initialize with UUID-based deanonymizer mapping
                uuid_mapping = UUIDDeanonymizerMapping(uuid_length=8)
                self.text_anonymizer = TextAnonymizer(
                    text_analyzer=self.text_analyzer,
                    deanonymizer_mapping=uuid_mapping,
                )

                if self.flat_pii_mapping:
                    gllm_mapping = self._convert_flat_to_gllm_format(self.flat_pii_mapping)
                    self.text_anonymizer._deanonymizer_mapping.update(gllm_mapping, use_uuid_suffix=False)

            except Exception as e:  # noqa: BLE001
                logger.warning(f"Failed to initialize GLLM Privacy components: {e}")
                self.enable_ner = False

    @classmethod
    def create_if_enabled(cls, pii_mapping: dict[str, str] | None = None) -> "ToolPIIHandler | None":
        """Create ToolPIIHandler when mappings or NER configuration exist.

        Args:
            pii_mapping: Existing PII mapping from runner service

        Returns:
            ToolPIIHandler instance when mapping or NER config is available, None otherwise
        """
        ner_api_url = os.getenv(NER_API_URL_ENV_VAR)
        ner_api_key = os.getenv(NER_API_KEY_ENV_VAR)

        if ner_api_url and ner_api_key:
            return cls(pii_mapping, ner_api_url, ner_api_key)

        if pii_mapping:
            return cls(pii_mapping)

        return None

    @classmethod
    def create_mapping_only(cls, pii_mapping: dict[str, str] | None = None) -> "ToolPIIHandler | None":
        """Create ToolPIIHandler in mapping-only mode (no NER).

        Args:
            pii_mapping: Existing PII mapping from runner service

        Returns:
            ToolPIIHandler instance when mapping exists, None otherwise
        """
        if not pii_mapping:
            return None

        return cls(pii_mapping)

    def deanonymize_tool_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Replace PII tags in tool arguments with real values.

        Recursively processes dictionaries, lists, and strings to replace all PII tags
        (e.g., '<EMAIL_1>') with their corresponding real values from flat_pii_mapping.

        Args:
            args: Tool arguments that may contain PII tags

        Returns:
            Arguments with tags replaced by real values
        """
        return self._process_value(args, operation=Operation.DEANONYMIZE)

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
        if isinstance(output, str):
            anonymized, updated_mapping = self._anonymize_text(output)
            return anonymized, updated_mapping
        elif isinstance(output, dict):
            anonymized, updated_mapping = self._anonymize_dict(output)
            return anonymized, updated_mapping
        else:
            # For non-string, non-dict outputs, return as-is
            return output, self.flat_pii_mapping

    @staticmethod
    def _convert_flat_to_gllm_format(
        flat_mapping: dict[str, str],
    ) -> dict[str, dict[str, str]]:
        """Convert flat PII mapping to GLLM Privacy nested format.

        Transforms flat format {'<PERSON_1>': 'Alice'} to nested format
        {'PERSON': {'<PERSON_1>': 'Alice'}} required by GLLM Privacy's internal state.

        Args:
            flat_mapping: Flat mapping (tag → value)

        Returns:
            Nested mapping organized by entity type
        """
        gllm_mapping: dict[str, dict[str, str]] = {}

        for tag, value in flat_mapping.items():
            tag_content = tag.strip("<>")
            parts = tag_content.rsplit("_", 1)
            entity_type = parts[0] if parts else "UNKNOWN"

            if entity_type not in gllm_mapping:
                gllm_mapping[entity_type] = {}

            gllm_mapping[entity_type][tag] = value

        return gllm_mapping

    @staticmethod
    def _convert_gllm_to_flat_format(
        gllm_mapping: dict[str, dict[str, str]],
    ) -> dict[str, str]:
        """Convert GLLM Privacy nested format back to flat format.

        Inverse of _convert_flat_to_gllm_format. Flattens nested structure
        {'PERSON': {'<PERSON_1>': 'Alice'}} back to {'<PERSON_1>': 'Alice'}.

        Args:
            gllm_mapping: Nested mapping from GLLM Privacy

        Returns:
            Flat mapping (tag → value)
        """
        flat_mapping: dict[str, str] = {}

        for entity_type, tags_dict in gllm_mapping.items():
            for tag, value in tags_dict.items():
                flat_mapping[tag] = value

        return flat_mapping

    def _deanonymize_text(self, text: str) -> str:
        """Deanonymize a single text string by replacing PII tags with real values.

        Uses GLLM Privacy's TextAnonymizer.deanonymize() when NER is enabled,
        otherwise falls back to simple string replacement. GLLM Privacy's deanonymize()
        doesn't require entities parameter as they're configured during TextAnalyzer init.

        Args:
            text: Text containing PII tags (e.g., '<EMAIL_1>', '<PERSON_1>')

        Returns:
            Text with PII tags replaced by their real values from flat_pii_mapping
        """
        if self.enable_ner and self.text_anonymizer:
            try:
                restored_text = self.text_anonymizer.deanonymize(text=text)
                return restored_text
            except Exception as e:
                logger.warning(f"GLLM Privacy deanonymization failed: {e}, falling back to simple replacement")
                return self._replace_tags_in_text(text)
        else:
            return self._replace_tags_in_text(text)

    def _anonymize_text(self, text: str) -> tuple[str, dict[str, str]]:
        """Anonymize PII in text using a two-phase approach.

        Phase 1: Masks known PII values using existing flat_pii_mapping (simple replacement).
        Phase 2: Uses NER (if enabled) to detect and mask NEW PII values not in mapping.
        Phase 3: Extracts newly discovered PII from GLLM Privacy's internal state.
        Phase 4-5: Converts and merges new mappings into flat_pii_mapping.

        Args:
            text: Text that may contain real PII values to be masked

        Returns:
            Tuple of (anonymized_text, updated_flat_pii_mapping including new discoveries)
        """
        anonymized = self._mask_with_existing_mapping(text)

        if self.enable_ner and self.text_anonymizer:
            try:
                result = self.text_anonymizer.anonymize(text=anonymized, entities=DEFAULT_SUPPORTED_ENTITIES)
                if hasattr(result, "text"):
                    anonymized = result.text
                else:
                    anonymized = result

                gllm_mapping = self.text_anonymizer.deanonymizer_mapping
                if gllm_mapping:
                    new_flat_mapping = self._convert_gllm_to_flat_format(gllm_mapping)
                    self.flat_pii_mapping.update(new_flat_mapping)
            except Exception as e:
                logger.warning(f"GLLM Privacy anonymization failed: {e}, continuing with masked text")

        return anonymized, self.flat_pii_mapping

    def _anonymize_dict(self, data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
        """Anonymize PII in dictionary recursively.

        Processes string values with _anonymize_text(), recursively handles nested dicts,
        and processes list items. Non-string/dict/list values are preserved as-is.

        Args:
            data: Dictionary that may contain PII values

        Returns:
            Tuple of (anonymized_dict, updated_mapping)
        """
        anonymized = {}

        for key, value in data.items():
            if isinstance(value, str):
                anonymized_value, _ = self._anonymize_text(value)
                anonymized[key] = anonymized_value
            elif isinstance(value, dict):
                anonymized[key], _ = self._anonymize_dict(value)
            elif isinstance(value, list):
                anonymized[key] = [self._anonymize_text(item)[0] if isinstance(item, str) else item for item in value]
            else:
                anonymized[key] = value

        return anonymized, self.flat_pii_mapping

    def _mask_with_existing_mapping(self, text: str) -> str:
        """Mask PII using existing flat mapping.

        Iterates through mapping in reverse order of value length to handle overlapping
        PII values correctly (longer values are replaced first).

        Args:
            text: Text to mask

        Returns:
            Text with known PII values replaced by tags
        """
        masked = text
        for tag, value in sorted(self.flat_pii_mapping.items(), key=lambda x: len(x[1]), reverse=True):
            if value in masked:
                masked = masked.replace(value, tag)
        return masked

    def _replace_tags_in_text(self, text: str) -> str:
        """Replace PII tags with real values in text using flat mapping.

        Args:
            text: Text containing PII tags

        Returns:
            Text with tags replaced by values
        """
        replaced = text
        for tag, value in self.flat_pii_mapping.items():
            if tag in replaced:
                replaced = replaced.replace(tag, value)
        return replaced

    def _process_value(self, value: Any, operation: Operation) -> Any:
        """Process a value recursively based on operation type.

        Args:
            value: Value to process
            operation: Operation enum value (ANONYMIZE or DEANONYMIZE)

        Returns:
            Processed value
        """
        if isinstance(value, str):
            if operation == Operation.DEANONYMIZE:
                return self._deanonymize_text(value)
            else:
                return self._anonymize_text(value)[0]
        elif isinstance(value, dict):
            return {k: self._process_value(v, operation) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._process_value(item, operation) for item in value]
        else:
            return value
