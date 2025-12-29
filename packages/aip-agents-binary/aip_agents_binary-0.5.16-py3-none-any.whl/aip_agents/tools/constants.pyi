from _typeshed import Incomplete
from enum import Enum, StrEnum

BOSA_API_BASE_URL: Incomplete
BOSA_API_KEY: Incomplete
BOSA_FETCH_MAX_RETRIES: int

class ToolType(StrEnum):
    """Tool types for BOSA Connector."""
    GLLM: str
    LANGCHAIN: str

class Action(Enum):
    """Actions for BOSA Connector."""
    GITHUB: str
    GOOGLE: str
    GOOGLE_DRIVE: str
    GOOGLE_MAIL: str
    TWITTER: str

class GitHubEndpoint(Enum):
    """GitHub endpoints for BOSA Connector."""
    INTEGRATIONS: str
    USER_HAS_INTEGRATION: str
    SUCCESS_AUTHORIZE_CALLBACK: str
    CREATE_ISSUE_HANDLER: str
    GET_ISSUE_HANDLER: str
    LIST_ISSUES: str
    LIST_ISSUES_COMMENTS: str
    SEARCH_ALL_ISSUES: str
    GET_COMMITS: str
    SEARCH_COMMITS: str
    GET_COLLABORATORS: str
    GET_RELEASES: str
    GET_CONTRIBUTORS: str
    GET_LANGUAGES: str
    SEARCH_CONTRIBUTIONS: str
    LIST_PULL_REQUESTS: str
    SEARCH_PR: str
    GET_PULL: str
    GET_ALL_CONTRIBUTOR_COMMIT_ACTIVITIES: str
    GET_COMMIT_ACTIVITY: str
    GET_WEEKLY_COMMIT_COUNTS: str
    GET_USER_CONTRIBUTION_STATISTICS: str
    LIST_PROJECT_ITEMS: str
    LIST_PROJECTS: str

class GoogleDriveEndpoint(Enum):
    """Google Drive endpoints for BOSA Connector."""
    INTEGRATIONS: str
    USER_HAS_INTEGRATION: str
    SUCCESS_AUTHORIZE_CALLBACK: str
    SEARCH_FILES: str
    GET_FILE: str
    CREATE_FILE: str
    CREATE_FOLDER: str
    UPDATE_FILE: str
    UPDATE_FOLDER: str
    COPY_FILE: str
    DELETE_FILE: str
    SUMMARIZE_FOLDER_FILES_BY_TYPE: str
    SUMMARIZE_TOTAL_FILES_BY_TYPE: str
    RECENT_FILES: str
    CREATE_PERMISSION: str
    LIST_PERMISSIONS: str
    GET_PERMISSION: str
    UPDATE_PERMISSION: str
    DELETE_PERMISSION: str
    DOWNLOAD_FILE: str

class GoogleDocsEndpoint(Enum):
    """Google Docs endpoints for BOSA Connector."""
    INTEGRATIONS: str
    USER_HAS_INTEGRATION: str
    SUCCESS_AUTHORIZE_CALLBACK: str
    GET_DOCUMENT: str
    LIST_DOCUMENTS: str
    CREATE_DOCUMENT: str
    UPDATE_DOCUMENT: str
    COPY_CONTENT: str
    UPDATE_DOCUMENT_MARKDOWN: str
    LIST_COMMENTS: str
    SUMMARIZE_COMMENTS: str

class GoogleEndpoint(Enum):
    """Google endpoints for BOSA Connector."""
    INTEGRATIONS: str
    USER_HAS_INTEGRATION: str
    SUCCESS_AUTHORIZE_CALLBACK: str
    USERINFO: str

class TwitterEndpoint(Enum):
    """Twitter endpoints for BOSA Connector."""
    INTEGRATIONS: str
    USER_HAS_INTEGRATION: str
    SUCCESS_AUTHORIZE_CALLBACK: str
    SEARCH: str
    GET_TWEETS: str
    GET_THREAD: str
    GET_USERS: str

class GoogleMailEndpoint(Enum):
    """Google Mail endpoints for BOSA Connector."""
    INTEGRATIONS: str
    USER_HAS_INTEGRATION: str
    SUCCESS_AUTHORIZE_CALLBACK: str
    CREATE_DRAFT: str
    LIST_DRAFTS: str
    SEND_DRAFT: str
    GET_DRAFT: str
    MODIFY_DRAFT: str
    LIST_LABELS: str
    LABEL_STATS: str
    GET_LABEL_DETAILS: str
    CREATE_LABELS: str
    MODIFY_LABELS: str
    DELETE_LABELS: str
    SEND_EMAIL: str
    LIST_EMAILS: str
    GET_EMAIL_DETAILS: str
    MODIFY_EMAIL: str
    DELETE_EMAIL: str
    TRASH_EMAIL: str
    UNTRASH_EMAIL: str
    LIST_THREADS: str
    THREAD_DETAILS: str
    MODIFY_THREAD: str
    GET_AUTO_REPLY: str
    SET_AUTO_REPLY: str
    GET_ATTACHMENT: str
    USERINFO: str

class ActionEndpointMap:
    """Maps Action enums to their corresponding Endpoint enums."""
    MAP: dict[Action, type[Enum]]
