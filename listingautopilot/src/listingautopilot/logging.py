"""Application logging setup.

This module keeps logging configuration small and explicit. Service modules
should use `get_logger(__name__)` and app entrypoints should call
`configure_logging()` once during startup.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Final


DEFAULT_LOG_LEVEL: Final[str] = "INFO"
DEFAULT_LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
DEFAULT_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    level: str | int | None = None,
    *,
    force: bool = False,
) -> None:
    selected_level = level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    numeric_level = (
        selected_level
        if isinstance(selected_level, int)
        else getattr(logging, selected_level.upper(), logging.INFO)
    )

    formatter = logging.Formatter(
        fmt=os.getenv("LOG_FORMAT", DEFAULT_LOG_FORMAT),
        datefmt=os.getenv("LOG_DATE_FORMAT", DEFAULT_DATE_FORMAT),
    )

    root_logger = logging.getLogger()
    if force:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)

    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(formatter)

    root_logger.setLevel(numeric_level)

    logging.getLogger("uvicorn.access").setLevel(
        getattr(logging, os.getenv("UVICORN_ACCESS_LOG_LEVEL", "WARNING").upper(), logging.WARNING)
    )
    logging.getLogger("sqlalchemy.engine").setLevel(
        getattr(logging, os.getenv("SQLALCHEMY_LOG_LEVEL", "WARNING").upper(), logging.WARNING)
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
