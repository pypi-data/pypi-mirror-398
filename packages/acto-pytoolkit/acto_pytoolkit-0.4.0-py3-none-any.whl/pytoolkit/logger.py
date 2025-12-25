import logging
import os
import sys
from typing import Optional


class _ColorFormatter(logging.Formatter):
    """Log formatter that adds color codes for console output.

    Colorization is only applied for stderr/stdout handlers on a TTY.
    """

    COLORS = {
        logging.DEBUG: "\033[37m",  # white
        logging.INFO: "\033[36m",  # cyan
        logging.WARNING: "\033[33m",  # yellow
        logging.ERROR: "\033[31m",  # red
        logging.CRITICAL: "\033[41m\033[37m",  # white on red background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        color = self.COLORS.get(record.levelno)
        if color and sys.stderr.isatty():
            return f"{color}{msg}{self.RESET}"
        return msg


def get_logger(
    name: Optional[str] = None,
    level: int = logging.INFO,
    with_colors: bool = True,
    to_file: Optional[str] = None,
) -> logging.Logger:
    """Create and configure a logger.

    Parameters
    ----------
    name:
        Name of the logger. If None, the root logger is used.
    level:
        Logging level to use for the logger.
    with_colors:
        If true, apply a color formatter for console output.
    to_file:
        Optional path for a log file. If provided, a file handler is attached.
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        formatter: logging.Formatter
        if with_colors:
            formatter = _ColorFormatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
        else:
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Optional file handler
        if to_file:
            file_handler = logging.FileHandler(to_file)
            file_formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(name)s\t%(message)s")
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        logger.propagate = False

    return logger


def configure_from_env(default_level: int = logging.INFO) -> logging.Logger:
    """Create a logger with its level controlled by LOG_LEVEL environment variable.

    Example values for LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL.
    """
    level_name = os.getenv("LOG_LEVEL", "").upper()
    level = getattr(logging, level_name, default_level)
    return get_logger(level=level)
