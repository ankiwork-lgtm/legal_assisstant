"""Centralised logging configuration for LegalLens AI.

A single :func:`get_logger` factory gives every module a child logger under
the ``legallens`` root so all log output can be controlled from one place.

Format
------
``%(asctime)s  %(levelname)-8s  %(name)s  %(message)s``

This plain-text format is captured verbatim by Vercel's log drain (stdout/
stderr of the Python serverless function) and is also easy to read in a local
terminal.

Log level
---------
Controlled by the ``LOG_LEVEL`` environment variable (default: ``INFO``).
Set ``LOG_LEVEL=DEBUG`` locally or in Vercel → Environment Variables to get
verbose output including prompt snippets and raw AI payloads.
"""

from __future__ import annotations

import logging
import os
import sys

# ---------------------------------------------------------------------------
# Root logger for the application
# ---------------------------------------------------------------------------

_ROOT_LOGGER_NAME = "legallens"

_LOG_FORMAT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _configure_root_logger() -> None:
    """Set up the root ``legallens`` logger exactly once."""
    root = logging.getLogger(_ROOT_LOGGER_NAME)

    # Respect LOG_LEVEL env var; fall back to INFO
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root.setLevel(level)

    # Avoid adding duplicate handlers if the module is reloaded (e.g. in tests)
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(handler)


_configure_root_logger()


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``legallens`` namespace.

    Parameters
    ----------
    name:
        Typically ``__name__`` of the calling module, e.g.
        ``app.routers.documents``.  The returned logger will be named
        ``legallens.<name>`` so its output is distinguishable in the log
        stream.

    Example
    -------
    >>> from app.utils.logger import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Processing request")
    """
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
