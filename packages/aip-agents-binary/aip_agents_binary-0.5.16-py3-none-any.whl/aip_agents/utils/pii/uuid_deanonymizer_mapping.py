"""UUID-based deanonymizer mapping utilities.

This module provides a UUID-based implementation of the deanonymizer mapping,
where anonymized entities are suffixed with UUIDs instead of sequential numbers.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import logging
import re
import uuid
from collections import defaultdict
from typing import Any

try:
    from gllm_privacy.pii_detector.utils.deanonymizer_mapping import (
        DeanonymizerMapping,
        MappingDataType,
    )
except ImportError:  # pragma: no cover
    MappingDataType = dict[str, dict[str, str]]

    class DeanonymizerMapping:  # type: ignore[no-redef]
        """Fallback deanonymizer mapping when optional dependency is missing.

        This class exists only to keep the module importable when `gllm-privacy`
        is not installed.
        """

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """Initialize the mapping.

            Raises:
                ImportError: Always raised because `gllm-privacy` is required.
            """
            raise ImportError("optional dependency 'gllm-privacy' is required for UUIDDeanonymizerMapping")


from aip_agents.utils.constants import DEFAULT_PII_TAG_NAMESPACE

logger = logging.getLogger(__name__)


def format_operator_with_uuid(operator_name: str, uuid_suffix: str) -> str:
    """Format the operator name with a UUID suffix.

    Args:
        operator_name: The operator name.
        uuid_suffix: The UUID suffix to append.

    Returns:
        The formatted operator name with UUID suffix.
    """
    clean_operator_name = re.sub(r"[<>]", "", operator_name)
    clean_operator_name = re.sub(r"_[a-f0-9-]+$", "", clean_operator_name)

    if operator_name.startswith("<") and operator_name.endswith(">"):
        return f"<{clean_operator_name}_{uuid_suffix}>"
    else:
        return f"{clean_operator_name}_{uuid_suffix}"


class UUIDDeanonymizerMapping(DeanonymizerMapping):
    """Class to store the deanonymizer mapping with UUID suffixes.

    This class extends DeanonymizerMapping to use UUID suffixes instead of
    sequential numbers for differentiating multiple entities of the same type.

    Attributes:
        mapping: The deanonymizer mapping.
        skip_format_duplicates: Whether to skip formatting duplicated operators.
        uuid_length: The length of the UUID suffix to use (default: 8).
    """

    def __init__(
        self,
        mapping: MappingDataType | None = None,
        skip_format_duplicates: bool = False,
        uuid_length: int = 8,
    ) -> None:
        """Initialize UUIDDeanonymizerMapping.

        Args:
            mapping: The deanonymizer mapping. If None, creates an empty defaultdict(dict).
            skip_format_duplicates: Whether to skip formatting duplicated operators.
            uuid_length: The length of the UUID suffix to use (default: 8).
        """
        if mapping is None:
            mapping = defaultdict(dict)

        try:
            super().__init__(mapping=mapping, skip_format_duplicates=skip_format_duplicates)
        except TypeError as exc:
            logger.warning(
                "DeanonymizerMapping init skipped due to incompatible signature; " "using local attributes only: %s",
                exc,
            )

        self.mapping = mapping
        self.skip_format_duplicates = skip_format_duplicates
        self.uuid_length = uuid_length

    def update(self, new_mapping: MappingDataType, use_uuid_suffix: bool | None = None) -> None:
        """Update the deanonymizer mapping with new values using UUID suffixes.

        Duplicated values will not be added. If there are multiple entities of the same type,
        the mapping will include a UUID suffix to differentiate them. For example, if there are
        two names in the input text, the mapping will include NAME_<uuid1> and NAME_<uuid2>.

        Args:
            new_mapping: The new mapping to be added to the existing deanonymizer mapping.
            use_uuid_suffix: Whether to apply UUID suffixes to keys.
                If True, keys will always be formatted with UUID suffixes.
                If False, keys will be used as-is without UUID formatting.
                If None, behavior falls back to the instance configuration via
                skip_format_duplicates (preserving existing behavior).

        Returns:
            None
        """
        seen_values: set[str] = set()
        format_with_uuid = self._should_format_with_uuid(use_uuid_suffix)

        for entity_type, values in new_mapping.items():
            self._update_entity_type(entity_type, values, seen_values, format_with_uuid)

    def _update_entity_type(
        self,
        entity_type: str,
        values: dict[str, str],
        seen_values: set[str],
        format_with_uuid: bool,
    ) -> None:
        """Update mapping entries for a single entity type.

        Args:
            entity_type: The entity category being updated.
            values: Mapping of anonymized keys to original values for the entity.
            seen_values: Set tracking values already processed in this update call.
            format_with_uuid: Whether UUID formatting should be applied to keys.

        Returns:
            None
        """
        for key, value in values.items():
            if not self._should_store_value(entity_type, value, seen_values):
                continue

            new_key = self._format_key(key, value, format_with_uuid)
            self.mapping[entity_type][new_key] = value
            seen_values.add(value)

    def _should_format_with_uuid(self, use_uuid_suffix: bool | None) -> bool:
        """Determine whether UUID suffix formatting is required.

        Args:
            use_uuid_suffix: Override controlling UUID formatting behavior.

        Returns:
            True if UUID suffixes should be applied, otherwise False.
        """
        if use_uuid_suffix is None:
            return not self.skip_format_duplicates
        return use_uuid_suffix

    def _should_store_value(self, entity_type: str, value: str, seen_values: set[str]) -> bool:
        """Check if the provided value should be stored in the mapping.

        Args:
            entity_type: Entity category being updated.
            value: Original value corresponding to the anonymized key.
            seen_values: Values already processed during this update call.

        Returns:
            True if the value is new for the entity type and current update scope.
        """
        return value not in seen_values and value not in self.mapping[entity_type].values()

    def _format_key(self, key: str, value: str, format_with_uuid: bool) -> str:
        """Return the appropriate key representation based on format flag.

        Args:
            key: Original anonymized key produced by the detector.
            value: Original value used to derive deterministic UUID suffixes.
            format_with_uuid: Whether UUID suffix formatting should be applied.

        Returns:
            The formatted key respecting the desired UUID formatting behavior.
        """
        if not format_with_uuid:
            return key

        uuid_suffix = uuid.uuid5(DEFAULT_PII_TAG_NAMESPACE, value).hex[: self.uuid_length]
        return format_operator_with_uuid(key, uuid_suffix)
