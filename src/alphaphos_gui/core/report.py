"""Load a search-engine report and summarise what was read."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import alphaphos as ap
import pandas as pd

from alphaphos_gui.constants import (
    MISSING_FILE,
    READ_FAILED,
    REPORT_SUFFIXES,
    RUN_COLUMN,
    WRONG_SUFFIX,
)


class ReportError(Exception):
    """A report could not be loaded; the message is shown to the user as-is."""


@dataclass(frozen=True)
class ReportSummary:
    source: Path
    n_rows_loaded: int
    n_rows_kept: int
    runs: tuple[str, ...]


def clean_path(text: str) -> Path:
    """Path from pasted text; Windows "Copy as path" wraps it in quotes."""
    return Path(text.strip().strip('"').strip("'"))


def load_report(path: Path) -> pd.DataFrame:
    """Read a Spectronaut report, turning every failure into a :class:`ReportError`."""
    if not path.is_file():
        raise ReportError(MISSING_FILE.format(path=path))
    if path.suffix.lower() not in REPORT_SUFFIXES:
        raise ReportError(WRONG_SUFFIX.format(name=path.name, suffixes=", ".join(REPORT_SUFFIXES)))
    try:
        return ap.read_spectronaut(path)
    except (ValueError, KeyError, OSError) as exc:
        raise ReportError(READ_FAILED.format(name=path.name, reason=exc)) from exc


def summarize(psm: pd.DataFrame) -> ReportSummary:
    attrs = psm.attrs
    return ReportSummary(
        source=Path(attrs["source_path"]),
        n_rows_loaded=int(attrs["n_rows_loaded"]),
        n_rows_kept=int(attrs["n_rows_returned"]),
        runs=tuple(sorted(psm[RUN_COLUMN].astype(str).unique())),
    )
