from _typeshed import Incomplete
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete
FILE_PATH_SYSTEM_NOTE: str
FILE_PATH_INACCESSIBLE_NOTE: str
FILE_URL_SYSTEM_NOTE: str

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
