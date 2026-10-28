"""State of one GUI session, independent of any web or UI library."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import alphaphos as ap
import plotly.graph_objects as go

from alphaphos_gui.constants import LOADED, NO_REPORT, UNEXPECTED
from alphaphos_gui.core.progress import Progress
from alphaphos_gui.core.report import (
    LoadedReport,
    ReportError,
    ReportSummary,
    load_proteome_report,
    load_report,
)

PHOSPHO, PROTEOME = "phospho", "proteome"


@dataclass
class ReportSlot:
    """One loaded report and the progress of loading it; each kind has its own."""

    loader: Callable[[Path, Progress], LoadedReport]
    loaded: LoadedReport | None = None
    progress: Progress = field(default_factory=Progress)

    @property
    def report(self) -> ReportSummary | None:
        return None if self.loaded is None else self.loaded.summary

    def load(self, path: Path) -> ReportSummary:
        """Replace the current report; on failure the previous one is kept.

        Reports each stage to :attr:`progress`, ending in ``done`` or ``error``.
        """
        try:
            loaded = self.loader(path, self.progress)
        except ReportError as exc:
            self.progress.error(str(exc))
            raise
        except Exception as exc:
            # Anything unexpected must still end the job, or the page waits forever.
            self.progress.error(UNEXPECTED.format(reason=exc))
            raise
        self.loaded = loaded
        self.progress.done(LOADED.format(name=path.name))
        return loaded.summary

    def contaminant_figure(self) -> go.Figure:
        if self.loaded is None:
            raise ReportError(NO_REPORT)
        return ap.viz.contaminant_fraction(self.loaded.contaminants)


@dataclass
class Session:
    slots: dict[str, ReportSlot] = field(
        default_factory=lambda: {
            PHOSPHO: ReportSlot(load_report),
            PROTEOME: ReportSlot(load_proteome_report),
        }
    )

    def __getitem__(self, kind: str) -> ReportSlot:
        return self.slots[kind]
