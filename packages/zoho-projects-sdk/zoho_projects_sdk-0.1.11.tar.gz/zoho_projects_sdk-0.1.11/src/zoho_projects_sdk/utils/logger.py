"""
Pre-configured logger for the SDK.
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Returns a pre-configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create a handler that writes to stdout
    handler = logging.StreamHandler(sys.stdout)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


# Example of how to use the logger in other modules:
# from .logger import get_logger
# logger = get_logger(__name__)
# logger.info("This is an info message.")
