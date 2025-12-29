"""LDF logging utilities."""

import logging
import os
import sys

# Default log level from environment
DEFAULT_LOG_LEVEL = os.getenv("LDF_LOG_LEVEL", "WARNING")

# Track if root logger has been configured
_configured = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module name.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance
    """
    # Strip ldf. prefix if present to avoid ldf.ldf.module
    if name.startswith("ldf."):
        name = name[4:]

    logger = logging.getLogger(f"ldf.{name}")
    return logger


def configure_logging(level: str | None = None, verbose: bool = False) -> None:
    """Configure logging for CLI usage.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR)
        verbose: If True, set level to DEBUG
    """
    global _configured

    if verbose:
        level = "DEBUG"
    elif level is None:
        level = DEFAULT_LOG_LEVEL

    # Get or create the root ldf logger
    root_logger = logging.getLogger("ldf")

    # Only add handler once
    if not _configured:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        _configured = True

    root_logger.setLevel(getattr(logging, level.upper()))
