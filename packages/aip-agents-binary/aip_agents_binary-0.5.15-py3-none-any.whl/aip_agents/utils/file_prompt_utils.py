"""Utilities for augmenting prompts with local file path notes.

This module adds file path metadata to queries but does not read file contents.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import os

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

FILE_PATH_SYSTEM_NOTE = (
    "\n\n[System Note: The user has provided a file named '{filename}'. "
    "It is available at the following local path: {path}]"
)
FILE_PATH_INACCESSIBLE_NOTE = (
    "\n\n[System Note: A file path was provided ({path}), but the file is not accessible. "
    "Please inform the user about this issue.]"
)
FILE_URL_SYSTEM_NOTE = (
    "\n\n[System Note: The file is also available at the following URL: {url} (expires in {expires_in} {hour_unit}).]"
)


def _normalize_file_entry(entry: str | dict[str, object]) -> dict[str, object] | None:
    """Normalize a single file entry into a dict.

    Args:
        entry: A string file path or a metadata dict.

    Returns:
        A normalized metadata dict or None if the entry is falsy.

    Raises:
        ValueError: If metadata dicts do not include a valid path.
    """
    if not entry:
        return None

    if isinstance(entry, str):
        return {"path": entry}

    if isinstance(entry, dict):
        path = entry.get("path") or entry.get("local_path")
        if not isinstance(path, str) or not path:
            raise ValueError("file metadata dicts must include a non-empty 'path'")
        return {
            "path": path,
            "filename": entry.get("filename"),
            "s3_url": entry.get("s3_url") or entry.get("url") or entry.get("file_uri"),
            "expires_in_hours": entry.get("expires_in_hours"),
        }

    raise ValueError("files must be a list of strings or dicts")


def _dedupe_file_entries(files: list[str | dict[str, object]]) -> list[dict[str, object]]:
    """Normalize and deduplicate file entries by their resolved path.

    Args:
        files: List of local filesystem paths or file metadata dicts.

    Returns:
        Deduplicated list of normalized dict entries.
    """
    seen: set[str] = set()
    deduped_entries: list[dict[str, object]] = []

    for raw_entry in files:
        try:
            normalized = _normalize_file_entry(raw_entry)
        except ValueError as exc:
            logger.warning(f"Skipping invalid file entry: {exc}")
            continue
        if not normalized:
            continue
        path_value = normalized.get("path")
        path = path_value if isinstance(path_value, str) else str(path_value)
        if path in seen:
            continue
        seen.add(path)
        deduped_entries.append(normalized)

    return deduped_entries


def _format_expiration_hours(expires_in_hours: object) -> tuple[object, str]:
    """Format expiration hours for display.

    Args:
        expires_in_hours: Expiration hours value.

    Returns:
        Tuple of (expires_value, hour_unit).
    """
    if isinstance(expires_in_hours, int):
        return expires_in_hours, "hour" if expires_in_hours == 1 else "hours"

    if isinstance(expires_in_hours, str) and expires_in_hours.isdigit():
        expires_value = int(expires_in_hours)
        return expires_value, "hour" if expires_value == 1 else "hours"

    return "unknown", "hours"


def _build_file_path_note(entry: dict[str, object]) -> str:
    """Build the system note for a file path entry.

    Args:
        entry: Normalized file metadata dict.

    Returns:
        System note string describing the file path accessibility.
    """
    path = str(entry["path"])
    is_accessible = os.path.isfile(path) and os.access(path, os.R_OK)
    if is_accessible:
        filename_value = entry.get("filename")
        filename = filename_value if isinstance(filename_value, str) and filename_value else os.path.basename(path)
        return FILE_PATH_SYSTEM_NOTE.format(filename=filename, path=path)

    logger.warning(f"File path is not accessible: {path}")
    return FILE_PATH_INACCESSIBLE_NOTE.format(path=path)


def _build_file_url_note(entry: dict[str, object]) -> str:
    """Build the system note for a file URL entry.

    Args:
        entry: Normalized file metadata dict.

    Returns:
        System note string describing the URL, or an empty string if no URL exists.
    """
    url = entry.get("s3_url")
    if not isinstance(url, str) or not url:
        return ""

    expires_value, hour_unit = _format_expiration_hours(entry.get("expires_in_hours"))
    return FILE_URL_SYSTEM_NOTE.format(
        url=url,
        expires_in=expires_value,
        hour_unit=hour_unit,
    )


def augment_query_with_file_paths(query: str, files: list[str | dict[str, object]]) -> str:
    """Augment query with file path system notes.

    Args:
        query: The original user query string.
        files: List of local filesystem paths or file metadata dicts to include.

    Returns:
        The query with system notes appended for each file path.

    Raises:
        ValueError: If files is not a list of strings or metadata dicts.
    """
    if not isinstance(files, list):
        raise ValueError("files must be a list of strings or dicts")

    deduped_entries = _dedupe_file_entries(files)

    if not deduped_entries:
        return query

    augmented_query = query
    for entry in deduped_entries:
        augmented_query += _build_file_path_note(entry)
        augmented_query += _build_file_url_note(entry)

    return augmented_query
