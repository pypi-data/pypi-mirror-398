# flake8: noqa: F401
"""AIP Agents Utils.

This module contains utility functions and classes for the AIP Agents package.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

from aip_agents.utils.artifact_helpers import (
    create_artifact_command,
    create_artifact_response,
    create_error_response,
    create_multiple_artifacts_command,
    create_text_artifact_response,
)
from aip_agents.utils.file_prompt_utils import augment_query_with_file_paths
from aip_agents.utils.final_response_builder import assemble_final_response
from aip_agents.utils.logger import LoggerManager, get_logger
from aip_agents.utils.reference_helper import (
    add_references_chunks,
    serialize_references_for_metadata,
    validate_references,
)
from aip_agents.utils.step_limit_manager import (
    _DELEGATION_CHAIN_CVAR,
    _DELEGATION_DEPTH_CVAR,
    _REMAINING_STEP_BUDGET_CVAR,
    _STEP_LIMIT_CONFIG_CVAR,
    StepExecutionContext,
    StepLimitManager,
)

# Optional PII imports - only import if dependencies are available
try:
    from aip_agents.utils.pii.pii_handler import ToolPIIHandler
    from aip_agents.utils.pii.pii_helper import (
        add_pii_mappings,
        extract_pii_mapping_from_agent_response,
    )

    _PII_AVAILABLE = True
except ImportError:
    _PII_AVAILABLE = False

# Build __all__ conditionally based on available dependencies
from aip_agents.utils.sse_chunk_transformer import SSEChunkTransformer

__all__ = [
    "get_logger",
    "LoggerManager",
    "create_artifact_response",
    "create_error_response",
    "create_artifact_command",
    "create_multiple_artifacts_command",
    "create_text_artifact_response",
    "validate_references",
    "serialize_references_for_metadata",
    "add_references_chunks",
    "assemble_final_response",
    "augment_query_with_file_paths",
    "SSEChunkTransformer",
    "StepExecutionContext",
    "StepLimitManager",
    "_DELEGATION_CHAIN_CVAR",
    "_DELEGATION_DEPTH_CVAR",
    "_REMAINING_STEP_BUDGET_CVAR",
    "_STEP_LIMIT_CONFIG_CVAR",
]

if _PII_AVAILABLE:
    __all__.extend(
        [
            "ToolPIIHandler",
            "add_pii_mappings",
            "extract_pii_mapping_from_agent_response",
        ]
    )
