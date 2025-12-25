import logging
import os

DEFAULT_LOG_LEVEL = os.getenv("RECKOMATE_SDK_LOG_LEVEL", "INFO").upper()


def get_logger(name: str = "reckomate_sdk") -> logging.Logger:
    """
    Create or return a configured SDK logger.
    """

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Prevent duplicate handlers

    logger.setLevel(DEFAULT_LOG_LEVEL)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s → %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
