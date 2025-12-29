"""Constants for Code Sandbox tool.

Authors:
    Komang Elang Surya Prawira (komang.e.s.prawira@gdplabs.id)
"""

# The filename `data.csv` is used as a hard-coded value because we currently lack a mechanism
# to dynamically determine the actual filename. This static filename is used for saving files
# inside the sandbox, and any pre-population steps will need to read from this filename.
# Code interacting with the sandbox can directly access the content of the file using the pre-defined variable,
# eliminating the need to load the file again. Agents or LLMs do not need to be aware of this filename.
DATA_FILE_NAME = "data.csv"
DATA_FILE_PATH = f"/files/{DATA_FILE_NAME}"
