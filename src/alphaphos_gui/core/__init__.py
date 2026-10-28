"""GUI logic with no web or UI dependency, testable with plain pytest."""

from alphaphos_gui.core.report import ReportError, ReportSummary, clean_path, load_report
from alphaphos_gui.core.session import Session

__all__ = ["ReportError", "ReportSummary", "Session", "clean_path", "load_report"]
