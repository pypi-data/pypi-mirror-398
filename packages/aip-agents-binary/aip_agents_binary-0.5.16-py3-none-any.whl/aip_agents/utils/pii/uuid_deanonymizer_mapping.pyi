from _typeshed import Incomplete
from aip_agents.utils.constants import DEFAULT_PII_TAG_NAMESPACE as DEFAULT_PII_TAG_NAMESPACE
from gllm_privacy.pii_detector.utils.deanonymizer_mapping import DeanonymizerMapping, MappingDataType
from typing import Any

MappingDataType = dict[str, dict[str, str]]

class DeanonymizerMapping:
    """Fallback deanonymizer mapping when optional dependency is missing.

        This class exists only to keep the module importable when `gllm-privacy`
        is not installed.
        """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the mapping.

            Raises:
                ImportError: Always raised because `gllm-privacy` is required.
            """

logger: Incomplete

def format_operator_with_uuid(operator_name: str, uuid_suffix: str) -> str:
    """Format the operator name with a UUID suffix.

    Args:
        operator_name: The operator name.
        uuid_suffix: The UUID suffix to append.

    Returns:
        The formatted operator name with UUID suffix.
    """

class UUIDDeanonymizerMapping(DeanonymizerMapping):
    """Class to store the deanonymizer mapping with UUID suffixes.

    This class extends DeanonymizerMapping to use UUID suffixes instead of
    sequential numbers for differentiating multiple entities of the same type.

    Attributes:
        mapping: The deanonymizer mapping.
        skip_format_duplicates: Whether to skip formatting duplicated operators.
        uuid_length: The length of the UUID suffix to use (default: 8).
    """
    mapping: Incomplete
    skip_format_duplicates: Incomplete
    uuid_length: Incomplete
    def __init__(self, mapping: MappingDataType | None = None, skip_format_duplicates: bool = False, uuid_length: int = 8) -> None:
        """Initialize UUIDDeanonymizerMapping.

        Args:
            mapping: The deanonymizer mapping. If None, creates an empty defaultdict(dict).
            skip_format_duplicates: Whether to skip formatting duplicated operators.
            uuid_length: The length of the UUID suffix to use (default: 8).
        """
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
