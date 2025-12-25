"""Logging helpers for the FinanFut SDK."""

from __future__ import annotations

import logging


DEFAULT_LOGGER_NAME = "finanfut_sdk"


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger configured for the SDK."""

    logger_name = name or DEFAULT_LOGGER_NAME
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    if logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)
    return logger
