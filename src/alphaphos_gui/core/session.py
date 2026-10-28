"""State of one GUI session, independent of any UI library."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from alphaphos_gui.core.report import ReportSummary, load_report, summarize


@dataclass
class Session:
    psm: pd.DataFrame | None = None
    report: ReportSummary | None = None

    def load(self, path: Path) -> ReportSummary:
        """Replace the current report; on failure the session is left unchanged."""
        psm = load_report(path)
        self.psm, self.report = psm, summarize(psm)
        return self.report
