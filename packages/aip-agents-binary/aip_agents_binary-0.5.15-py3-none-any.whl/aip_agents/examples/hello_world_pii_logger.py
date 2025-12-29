"""This example shows how to use the get_logger function to initialize a logger with PII logging enabled.

Authors:
    Saul Sayers (saul.sayers@gdplabs.id)
"""

import logging

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__, logging.DEBUG)

# Set up logging format
sensitive_info = (
    "contoh nomor ktp 3525011212941001\n"
    "contoh email john.doe@example.com\n"
    "contoh nomor telepon +628121729819 dan 0812898029384.\n"
    "contoh npwp 01.123.456.7-891.234"
)

logger.info(f"Logging sensitive information for processing: \n{sensitive_info}")
