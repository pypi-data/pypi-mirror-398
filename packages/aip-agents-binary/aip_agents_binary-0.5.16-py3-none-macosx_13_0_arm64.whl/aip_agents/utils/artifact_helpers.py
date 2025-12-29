"""Utility functions for artifact handling in agent tools.

This module provides standardized functions for creating artifact responses
that are compatible with the A2A protocol and the agent's artifact handling system.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import base64
import hashlib
from typing import Any

from deprecated import deprecated
from langgraph.types import Command
from pydantic import ValidationError

from aip_agents.a2a.types import Artifact, ArtifactType, MimeType, get_mime_type_from_filename


class ArtifactHandler:
    """Handler class for creating and managing artifacts in agent tools.

    This class provides a clean, object-oriented interface for artifact creation
    with built-in validation, deduplication, and standardized formatting.
    """

    def __init__(self):
        """Initialize the ArtifactHandler."""
        self._artifact_cache: dict[str, dict[str, Any]] = {}

    @deprecated(version="0.5.0", reason="Use create_artifact(...) which handles text and binary.")
    def create_file_artifact(  # noqa: PLR0913
        self,
        result: str,
        artifact_data: bytes | str,
        artifact_name: str,
        artifact_description: str = "",
        mime_type: str | None = None,
        enable_deduplication: bool = True,
    ) -> dict[str, Any]:
        """Deprecated. Use create_artifact instead.

        Args:
            result (str): The message/result to show to the agent.
            artifact_data (bytes | str): The binary data for the artifact.
            artifact_name (str): The name for the artifact file.
            artifact_description (str, optional): Description of the artifact. Defaults to "".
            mime_type (str | None, optional): MIME type of the artifact. If None, will be auto-detected.
            enable_deduplication (bool, optional): Whether to deduplicate by content hash. Defaults to True.

        Returns:
            dict[str, Any]: Dictionary with 'result' and 'artifact' keys.
        """
        return self.create_artifact(
            result=result,
            data=artifact_data,
            artifact_name=artifact_name,
            artifact_description=artifact_description,
            mime_type=mime_type,
            enable_deduplication=enable_deduplication,
        )

    @deprecated(version="0.5.0", reason="Use create_artifact(...) which handles text and binary.")
    def create_text_artifact(  # noqa: PLR0913
        self,
        result: str,
        artifact_text: str,
        artifact_name: str,
        artifact_description: str = "",
        mime_type: str | None = None,
        enable_deduplication: bool = True,
    ) -> dict[str, Any]:
        """Deprecated. Use create_artifact instead.

        Args:
            result (str): The message/result to show to the agent.
            artifact_text (str): The text content for the artifact.
            artifact_name (str): The name for the artifact file.
            artifact_description (str, optional): Description of the artifact. Defaults to "".
            mime_type (str | None, optional): MIME type of the artifact. If None, will be auto-detected.
            enable_deduplication (bool, optional): Whether to deduplicate by content hash. Defaults to True.

        Returns:
            dict[str, Any]: Dictionary with 'result' and 'artifact' keys.
        """
        return self.create_artifact(
            result=result,
            data=artifact_text,
            artifact_name=artifact_name,
            artifact_description=artifact_description,
            mime_type=mime_type,
            enable_deduplication=enable_deduplication,
        )

    def create_artifact(  # noqa: PLR0913
        self,
        result: str,
        data: bytes | str,
        artifact_name: str,
        artifact_description: str = "",
        mime_type: str | None = None,
        enable_deduplication: bool = True,
    ) -> dict[str, Any]:
        """Create an artifact with automatic text/binary handling.

        Args:
            result: The message/result to show to the agent.
            data: The data for the artifact. Bytes for binary; str for text or base64.
            artifact_name: The filename to present to users.
            artifact_description: Description of the artifact.
            mime_type: Optional MIME type. If None, inferred from filename.
            enable_deduplication: Whether to deduplicate by content hash.

        Returns:
            Dictionary with 'result' and 'artifact' keys.
        """
        inferred_mime = self._infer_mime_type(artifact_name, mime_type)
        is_text_like = self._is_text_mime(inferred_mime)

        artifact_b64 = self._encode_to_base64(data, treat_as_text=is_text_like)
        effective_mime = (
            inferred_mime
            if not is_text_like or inferred_mime != MimeType.APPLICATION_OCTET_STREAM
            else MimeType.TEXT_PLAIN
        )

        # Deduplication check
        if enable_deduplication:
            artifact_hash = self.generate_artifact_hash(artifact_b64, artifact_name, effective_mime)
            cached = self._artifact_cache.get(artifact_hash)
            if cached:
                return {
                    "result": f"Using cached artifact: {cached['artifact']['name']}",
                    "artifact": cached["artifact"],
                }

        artifact_payload = self._build_artifact_payload(
            b64_data=artifact_b64,
            name=artifact_name,
            description=artifact_description,
            mime=effective_mime,
        )

        response = {"result": result, "artifact": artifact_payload}

        if enable_deduplication:
            artifact_hash = self.generate_artifact_hash(artifact_b64, artifact_name, effective_mime)
            self._artifact_cache[artifact_hash] = response

        return response

    def _infer_mime_type(self, artifact_name: str, override_mime_type: str | None) -> str:
        """Return explicit MIME if provided; otherwise infer from filename.

        Args:
            artifact_name (str): The name of the artifact.
            override_mime_type (str | None): The MIME type to override.

        Returns:
            str: The inferred MIME type.
        """
        return override_mime_type or get_mime_type_from_filename(artifact_name)

    def _is_text_mime(self, mime: str) -> bool:
        """Check whether a MIME type should be treated as text content.

        Args:
            mime (str): The MIME type to check.

        Returns:
            bool: True if the MIME type should be treated as text content, False otherwise.
        """
        return mime.startswith("text/") or mime == MimeType.APPLICATION_JSON

    def _encode_to_base64(self, data: bytes | str, treat_as_text: bool) -> str:
        """Encode data to base64 according to handling rules for text/binary.

        - For text: always base64-encode UTF-8 bytes
        - For binary: bytes are base64-encoded; str is assumed already base64

        Args:
            data (bytes | str): The data to encode.
            treat_as_text (bool): Whether to treat the data as text.

        Returns:
            str: The base64 encoded data.
        """
        if treat_as_text:
            if isinstance(data, str):
                raw = data.encode("utf-8")
            elif isinstance(data, bytes):
                raw = data
            else:
                raise TypeError("data must be bytes or str")
            return base64.b64encode(raw).decode("utf-8")

        # binary path
        if isinstance(data, bytes):
            return base64.b64encode(data).decode("utf-8")
        if isinstance(data, str):
            return data
        raise TypeError("data must be bytes or str")

    def _build_artifact_payload(self, b64_data: str, name: str, description: str, mime: str) -> dict[str, Any]:
        """Construct a validated artifact payload as a dict via the Artifact model.

        Args:
            b64_data (str): Base64 encoded data.
            name (str): Artifact name.
            description (str): Artifact description.
            mime (str): MIME type.

        Returns:
            dict[str, Any]: Dictionary with 'artifact_type', 'data', 'name', 'description', and 'mime_type' keys.
        """
        return Artifact(
            artifact_type=ArtifactType.FILE,
            data=b64_data,
            name=name,
            description=description,
            mime_type=mime,
        ).model_dump()

    def create_error_response(self, error_message: str) -> str:
        """Create a standardized error response for tools.

        Args:
            error_message: The error message to return.

        Returns:
            String with error information.
        """
        return f"Error: {error_message}"

    def clear_cache(self) -> None:
        """Clear the artifact cache."""
        self._artifact_cache.clear()

    def get_cache_size(self) -> int:
        """Get the number of cached artifacts.

        Returns:
            Number of artifacts in cache.
        """
        return len(self._artifact_cache)

    @staticmethod
    def generate_artifact_hash(artifact_data: str, name: str, mime_type: str) -> str:
        """Generate a hash for artifact deduplication.

        Args:
            artifact_data: Base64 encoded artifact data.
            name: Artifact name.
            mime_type: MIME type.

        Returns:
            Hash string for deduplication.
        """
        content = f"{artifact_data}:{name}:{mime_type}"
        return hashlib.sha256(content.encode()).hexdigest()


# Global instance for convenience
_default_handler = ArtifactHandler()


@deprecated(version="0.5.0", reason="Use create_artifact_command(...) which returns a Command update.")
def create_artifact_response(  # noqa: PLR0913
    result: str,
    artifact_data: bytes | str,
    artifact_name: str,
    artifact_description: str = "",
    mime_type: str | None = None,
) -> dict[str, Any]:
    r"""Create a standardized artifact response for tools.

    This function creates a response that separates the agent-facing result
    from the user-facing artifact, following the established pattern for
    artifact generation in the agent system.

    Args:
        result: The message/result to show to the agent (clean, no file data).
        artifact_data: The binary data or base64 string for the artifact.
        artifact_name: The name for the artifact file.
        artifact_description: Description of the artifact. Defaults to "".
        mime_type: MIME type of the artifact. If None, will be auto-detected from filename.

    Returns:
        Dictionary with 'result' and 'artifacts' keys (artifacts is always a list).

    Example:
        >>> import io
        >>> csv_data = "Name,Age\\nAlice,30\\nBob,25"
        >>> response = create_artifact_response(
        ...     result="Generated a 2-row CSV table",
        ...     artifact_data=csv_data.encode('utf-8'),
        ...     artifact_name="data.csv",
        ...     artifact_description="Sample data table",
        ...     mime_type="text/csv"
        ... )
        >>> assert "result" in response
        >>> assert "artifacts" in response
        >>> assert isinstance(response["artifacts"], list)
    """
    single_artifact = _default_handler.create_artifact(
        result=result,
        data=artifact_data,
        artifact_name=artifact_name,
        artifact_description=artifact_description,
        mime_type=mime_type,
        enable_deduplication=False,
    )

    # Convert single artifact to list format
    return {"result": single_artifact["result"], "artifacts": [single_artifact["artifact"]]}


@deprecated(version="0.5.0", reason="Use create_artifact_command(...) which handles text and binary.")
def create_text_artifact_response(
    result: str,
    artifact_text: str,
    artifact_name: str,
    artifact_description: str = "",
    mime_type: str | None = None,
) -> dict[str, Any]:
    """Create a standardized artifact response for tools.

    Args:
        result: The message/result to show to the agent.
        artifact_text: The text content for the artifact.
        artifact_name: The name for the artifact file.
        artifact_description: Description of the artifact.
        mime_type: MIME type of the artifact. If None, will be auto-detected from filename.

    Returns:
        Dictionary with 'result' and 'artifacts' keys (artifacts is always a list).
    """
    return _default_handler.create_artifact(
        result=result,
        data=artifact_text,
        artifact_name=artifact_name,
        artifact_description=artifact_description,
        mime_type=mime_type,
        enable_deduplication=False,
    )


@deprecated(version="0.5.0", reason="Use create_artifact_command(...) and compose updates instead of dict responses.")
def create_multiple_artifacts_response(result: str, artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a standardized response for multiple artifacts.

    Args:
        result: The message/result to show to the agent.
        artifacts: List of artifact dictionaries.

    Returns:
        Dictionary with 'result' and 'artifacts' keys.
    """
    return {"result": result, "artifacts": artifacts}


def create_artifact_command(  # noqa: PLR0913
    result: str,
    artifact_data: bytes | str,
    artifact_name: str,
    artifact_description: str = "",
    mime_type: str | None = None,
    metadata_update: dict[str, Any] | None = None,
) -> Command:
    """Create a Command that updates artifacts (and optional metadata).

    Args:
        result: Message/result to show to the agent (for ToolMessage content).
        artifact_data: The binary data or base64 string for the artifact.
        artifact_name: The name for the artifact file.
        artifact_description: Description of the artifact.
        mime_type: MIME type of the artifact. If None, auto-detected from filename.
        metadata_update: Optional metadata delta to merge into state metadata.

    Returns:
        Command: A LangGraph Command with update containing 'result', 'artifacts', and optional 'metadata'.
    """
    single = _default_handler.create_artifact(
        result=result,
        data=artifact_data,
        artifact_name=artifact_name,
        artifact_description=artifact_description,
        mime_type=mime_type,
        enable_deduplication=False,
    )
    update: dict[str, Any] = {
        "result": single["result"],
        "artifacts": [single["artifact"]],
    }
    if metadata_update:
        update["metadata"] = metadata_update
    return Command(update=update)


def create_multiple_artifacts_command(
    result: str,
    artifacts: list[Artifact | dict[str, Any]] | None = None,
    metadata_update: dict[str, Any] | None = None,
) -> Command:
    """Create a Command that updates multiple artifacts (and optional metadata).

    The 'artifacts' list accepts mixed item types:
    - Artifact: a typed artifact model (preferred). Will be converted via model_dump().
    - dict: a prebuilt artifact dict ready for A2A.
    - DataSpec dict: raw spec to build an artifact with keys:
        {'data': bytes|str, 'artifact_name': str, 'artifact_description'?: str, 'mime_type'?: str}

    Args:
        result: Message/result to show to the agent.
        artifacts: List of items (Artifact | dict) to attach or build.
        metadata_update: Optional metadata delta to merge into state metadata.

    Returns:
        Command: A LangGraph Command with update containing 'result', 'artifacts', and optional 'metadata'.
    """
    built_artifacts: list[dict[str, Any]] = []
    if not artifacts:
        raise ValueError("At least one of 'artifacts' must be provided and non-empty")

    for art in artifacts or []:
        if isinstance(art, Artifact):
            built_artifacts.append(art.model_dump())
        elif isinstance(art, dict):
            try:
                validated = Artifact.model_validate(art)
            except ValidationError as e:
                raise ValueError(f"Invalid artifact dict: {e}") from e
            built_artifacts.append(validated.model_dump())
        else:
            raise TypeError("artifacts items must be Artifact or dict")

    update: dict[str, Any] = {"result": result, "artifacts": built_artifacts}
    if metadata_update:
        update["metadata"] = metadata_update
    return Command(update=update)


def create_error_response(error_message: str) -> str:
    """Create a standardized error response for tools.

    For error cases, we return a simple string that will be passed directly
    to the agent without any artifact processing.

    Args:
        error_message: The error message to return.

    Returns:
        String with error information.
    """
    return _default_handler.create_error_response(error_message)


def extract_artifacts_from_agent_response(result: Any) -> tuple[str, list[dict[str, Any]]]:
    """Extract artifacts from agent response for delegation tools.

    Args:
        result: The result returned by the delegated agent.

    Returns:
        Tuple of (text_response, artifacts_list) where:
        - text_response: The text content for the agent
        - artifacts_list: List of artifacts to be passed through
    """
    if not isinstance(result, dict):
        return str(result), []

    text_response = result.get("output", str(result))
    artifacts = result.get("full_final_state", {}).get("artifacts", [])

    # Ensure artifacts is a list before returning
    if not isinstance(artifacts, list):
        artifacts = []

    return str(text_response), artifacts


def create_delegation_response_with_artifacts(
    result: str, artifacts: list[dict[str, Any]], agent_name: str = ""
) -> Command:
    """Create a delegation response that includes artifacts only when needed.

    Args:
        result: The text result from the delegated agent.
        artifacts: List of artifacts from the delegated agent (always a list).
        agent_name: Name of the agent for prefixing the result.

    Returns:
        Command containing 'result' and optional 'artifacts'.
    """
    # Format the result text with agent attribution
    formatted_result = f"[{agent_name}] {result}" if agent_name else result

    update: dict[str, Any] = {"result": formatted_result}
    if artifacts:
        update["artifacts"] = artifacts
    return Command(update=update)
