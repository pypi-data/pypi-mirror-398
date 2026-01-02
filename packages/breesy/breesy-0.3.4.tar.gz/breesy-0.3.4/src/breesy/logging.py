import logging
import sys

logger = logging.getLogger("breesy")
logger.setLevel(logging.INFO)

# Prevent bubbling of messages to root logger (avoid duplicates)
logger.propagate = False

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))  # e.g.: logger.warning("hello") -> "WARNING: hello"
logger.addHandler(_handler)

def set_log_level(level: str = "INFO") -> None:
    """Set logging verbosity level for the whole Breesy package.

    :param level: One of 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}. Use one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    logger.setLevel(numeric_level)


def silence_logs() -> None:
    """Silence all Breesy log messages."""
    logger.setLevel(logging.CRITICAL + 1)  # Higher than any level


def enable_logs(level: str = "INFO") -> None:
    """Re-enable Breesy log messages after silencing.

    :param level: The log level to restore. Default is 'INFO'.
    """
    set_log_level(level)