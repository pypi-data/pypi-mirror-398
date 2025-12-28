"""Structured logging for dossier-tools.

Configure via environment:
  DOSSIER_LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (default: WARNING)

Example:
  DOSSIER_LOG_LEVEL=DEBUG dossier verify workflow.ds.md
"""

from __future__ import annotations

import logging
import os
import sys

# Package-level logger
logger = logging.getLogger("dossier_tools")


def configure_logging() -> None:
    """Configure logging based on environment.

    Logs to stderr to avoid interfering with CLI output.
    """
    level_name = os.environ.get("DOSSIER_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logger.setLevel(level)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a child logger for a module.

    Args:
        name: Module name (e.g., 'registry', 'signing')

    Returns:
        Logger instance
    """
    return logger.getChild(name)
