"""Shared utilities: logging setup and safe file IO.

Logging (not print) is used across the pipeline so runs are timestamped,
levelled, and captured to a file for later inspection -- the difference
between a script and something you can operate.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

from config import LOG_DIR


def get_logger(name: str = "pipeline") -> logging.Logger:
    """Return a configured logger writing to both console and a log file.

    Handlers are only added once, so repeated calls from different modules
    reuse the same configuration instead of duplicating output.
    """
    logger = logging.getLogger(name)
    if logger.handlers:  # already configured
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S"
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_DIR / f"{name}.log", mode="w")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except OSError as exc:  # non-fatal: keep running with console output only
        logger.warning("Could not open log file (%s). Console logging only.", exc)

    return logger


def read_csv_safe(path: Path, logger: logging.Logger | None = None) -> pd.DataFrame:
    """Read a CSV with actionable errors instead of a bare traceback."""
    log = logger or get_logger()
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        log.error("File not found: %s", path)
        raise
    except pd.errors.EmptyDataError:
        log.error("File is empty: %s", path)
        raise
    except pd.errors.ParserError as exc:
        log.error("Could not parse %s -- check the delimiter/encoding: %s", path, exc)
        raise
    log.info("Read %s rows x %s cols from %s", f"{len(df):,}", df.shape[1], path.name)
    return df


def write_csv_safe(df: pd.DataFrame, path: Path,
                   logger: logging.Logger | None = None) -> None:
    """Write a CSV, creating parent directories and reporting failures clearly."""
    log = logger or get_logger()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
    except OSError as exc:
        log.error("Could not write %s: %s", path, exc)
        raise
    log.info("Wrote %s rows -> %s", f"{len(df):,}", path)
