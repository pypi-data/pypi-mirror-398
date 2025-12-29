# topdogalerts/listener/logging.py
"""
Logging configuration for topdogalerts listeners.
"""
import logging
import os


def configure_listener_logging(listener_name: str) -> logging.Logger:
    """
    Configure and return a logger for a listener.

    Reads LOG_LEVEL from environment (defaults to INFO) and sets up
    a standardized log format.

    Args:
        listener_name: The name of the listener (used as logger name).

    Returns:
        A configured logger instance.

    Example:
        logger = configure_listener_logging("record_high")
        logger.info("Listener started")
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    return logging.getLogger(listener_name)
