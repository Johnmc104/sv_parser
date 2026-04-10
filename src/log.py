"""
Logging configuration for rtl_scan.

Library modules use ``logging.getLogger(__name__)`` for structured logging.
The CLI configures the root logger via ``setup_logging()``.
"""

import logging
import sys

_LOG_FORMAT = "%(levelname)-5s %(name)s: %(message)s"
_LOG_FORMAT_DEBUG = "%(levelname)-5s %(name)s [%(filename)s:%(lineno)d]: %(message)s"


def setup_logging(verbose=0, quiet=False):
    # type: (int, bool) -> None
    """Configure logging for CLI usage.

    Args:
        verbose: 0 = WARNING, 1 = INFO, 2+ = DEBUG
        quiet:   suppress all log output (ERROR only)
    """
    if quiet:
        level = logging.ERROR
    elif verbose >= 2:
        level = logging.DEBUG
    elif verbose >= 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    fmt = _LOG_FORMAT_DEBUG if verbose >= 2 else _LOG_FORMAT

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger("src")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
