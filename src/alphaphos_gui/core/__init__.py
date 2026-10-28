"""GUI logic with no web or UI dependency, testable with plain pytest."""

from alphaphos_gui.core.progress import Progress, ProgressState
from alphaphos_gui.core.report import (
    LoadedReport,
    ReportError,
    ReportSummary,
    clean_path,
    load_proteome_report,
    load_report,
)
from alphaphos_gui.core.session import PHOSPHO, PROTEOME, ReportSlot, Session

__all__ = [
    "PHOSPHO",
    "PROTEOME",
    "LoadedReport",
    "Progress",
    "ProgressState",
    "ReportError",
    "ReportSlot",
    "ReportSummary",
    "Session",
    "clean_path",
    "load_proteome_report",
    "load_report",
]
