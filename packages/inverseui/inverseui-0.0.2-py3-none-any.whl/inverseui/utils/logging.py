"""Logging configuration for InverseUI Runtime."""

import logging
import sys
from pathlib import Path

import structlog

from inverseui.config import paths


def setup_logging(log_file: Path | None = None, level: int = logging.INFO) -> None:
    """Configure structured logging."""
    # Use daemon log file if not specified
    if log_file is None:
        paths.ensure_dirs()
        log_file = paths.daemon_log

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=level,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a configured logger."""
    return structlog.get_logger(name)
