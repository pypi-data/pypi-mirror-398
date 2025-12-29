"""Generic Constants for AIP Agents components.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import os

# Base directory of the project
# Note: This might need adjustment depending on how aip_agents is used as a library.
#       Consider if this is truly needed in the generic package.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Agent settings
DEFAULT_AGENT_TIMEOUT = 120  # seconds

# Chat history settings - These might also be application-specific,
# but are kept here for now as they are often used by generic agent logic.
LAST_N_CHATS = 10  # Number of previous chat pairs to include in history
MAX_MEMORY_TOKENS = 32000  # Maximum tokens allowed in memory

# Logging settings
TEXT_PREVIEW_LENGTH = 50  # Maximum length for text previews in logs
