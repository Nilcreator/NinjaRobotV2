import logging
import sys
from .config import settings


def setup_logger(name: str) -> logging.Logger:
    """
    Sets up a logger with the specified name and configuration from settings.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Prevent adding multiple handlers if setup_logger is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Set level based on settings
        level = getattr(logging, str(settings.LOG_LEVEL).upper(), logging.INFO)
        logger.setLevel(level)

    return logger
