import logging
import sys

LOGGER_NAME = "kolena.agents"
logger = logging.getLogger(LOGGER_NAME)


def enable_verbose_stdout_logging() -> None:
    """Enables verbose logging to stdout. This is useful for debugging."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
