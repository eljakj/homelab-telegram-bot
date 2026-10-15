"""Logging setup — replaces the old script's bare `print()` calls."""

from __future__ import annotations

import logging
import os
import sys


def setup_logging() -> None:
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    # These two libraries are very chatty on INFO/DEBUG; keep them quiet
    # unless we're actively debugging HTTP traffic.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
