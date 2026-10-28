"""Load phospho and proteome reports, measure their contaminants, and summarise what was read."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import alphaphos as ap
import pandas as pd
from alphaphos.io.contaminants import filter_contaminants
from alphaphos.qc.psm_metrics import compute_contaminant_fraction_per_sample

from alphaphos_gui.constants import (
    DIANN_LONG_UNSUPPORTED,
    MISSING_FILE,
    READ_FAILED,
    REPORT_SUFFIXES,
    RUN_COLUMN,
    STAGE_CONTAMINANTS,
    STAGE_FILTERING,
    STAGE_PARSING,
    STAGE_READING,
    UNIT_PROTEIN_GROUPS,
    UNIT_ROWS,
    WRONG_SUFFIX,
)
from alphaphos_gui.core.progress import Progress


class ReportError(Exception):
    """A report could not be loaded; the message is shown to the user as-is."""


@dataclass(frozen=True)
class ReportSummary:
    source: Path
    layout: str  # e.g. "Spectronaut long", "DIA-NN short"
    unit: str  # what the counts count: precursor rows, or protein groups
    n_loaded: int
    n_kept: int  # after contaminants (and the reader's own filters) are removed
    runs: tuple[str, ...]


@dataclass(frozen=True)
class LoadedReport:
    data: Any  # PSM DataFrame (precursor reports) or protein AnnData (short reports)
    contaminants: pd.DataFrame  # per-run contaminant fraction, measured before removal
    summary: ReportSummary


def clean_path(text: str) -> Path:
    """Path from pasted text; Windows "Copy as path" wraps it in quotes."""
    return Path(text.strip().strip('"').strip("'"))


def _check_path(path: Path) -> None:
    if not path.is_file():
        raise ReportError(MISSING_FILE.format(path=path))
    if path.suffix.lower() not in REPORT_SUFFIXES:
        raise ReportError(WRONG_SUFFIX.format(name=path.name, suffixes=", ".join(REPORT_SUFFIXES)))


def _contaminant_settings() -> tuple[tuple[str, ...], Any]:
    """The reader's own contaminant prefixes and FASTA, so every path agrees."""
    settings = ap.resolve_io_settings(None)
    return tuple(settings["contaminant_prefixes"]), settings["contaminants_fasta"]


def _runs(psm: pd.DataFrame) -> tuple[str, ...]:
    return tuple(sorted(psm[RUN_COLUMN].astype(str).unique()))


def load_report(path: Path, progress: Progress | None = None) -> LoadedReport:
    """Read a Spectronaut phospho report once, keeping contaminants long enough to measure them.

    Reading with contaminants kept and then applying the reader's own filter
    with the reader's own settings gives exactly what ``read_spectronaut``
    returns by default, without reading the file twice.  Every failure
    becomes a :class:`ReportError`.
    """
    progress = progress or Progress()
    _check_path(path)
    prefixes, fasta = _contaminant_settings()

    def on_bytes(done: int, total: int) -> None:
        # Parquet delivers all bytes early and decodes afterwards, so once every
        # byte is in, the rest of the read is an unmeasurable parsing stage.
        if done < total:
            progress.stage(STAGE_READING, done / total)
        else:
            progress.stage(STAGE_PARSING)

    progress.stage(STAGE_READING, 0.0)
    try:
        raw = ap.read_spectronaut(path, advanced={"drop_contaminants": False}, progress=on_bytes)
    except (ValueError, KeyError, OSError) as exc:
        raise ReportError(READ_FAILED.format(name=path.name, reason=exc)) from exc

    progress.stage(STAGE_CONTAMINANTS)
    contaminants = compute_contaminant_fraction_per_sample(
        raw, contaminant_prefixes=prefixes, contaminants_fasta=fasta
    )
    progress.stage(STAGE_FILTERING)
    psm = filter_contaminants(raw, contaminants_fasta=fasta, prefix_patterns=prefixes)

    summary = ReportSummary(
        source=path,
        layout="Spectronaut long",
        unit=UNIT_ROWS,
        n_loaded=int(raw.attrs["n_rows_loaded"]),
        n_kept=len(psm),
        runs=_runs(psm),
    )
    return LoadedReport(data=psm, contaminants=contaminants, summary=summary)


def load_proteome_report(path: Path, progress: Progress | None = None) -> LoadedReport:
    """Read a proteome report in whichever format its header shows.

    Short reports (Spectronaut or DIA-NN protein-group matrices) become a
    protein AnnData; contaminant protein groups are measured, then removed.
    Spectronaut long reports go through the precursor path, like phospho.
    The readers report no byte progress, so reading is one unmeasured stage.
    """
    progress = progress or Progress()
    _check_path(path)
    prefixes, fasta = _contaminant_settings()

    progress.stage(STAGE_READING)
    try:
        fmt = ap.proteome.detect_report_format(path)
        if fmt.level == "long" and fmt.engine == "DIA-NN":
            raise ReportError(DIANN_LONG_UNSUPPORTED)
        if fmt.level == "long":
            raw = ap.proteome.read_spectronaut_long(path, drop_contaminants=False)
        elif fmt.engine == "Spectronaut":
            adata = ap.proteome.read_spectronaut_short(path)
        else:
            adata = ap.proteome.read_diann_pg_matrix(path)
    except (ValueError, KeyError, OSError) as exc:
        raise ReportError(READ_FAILED.format(name=path.name, reason=exc)) from exc

    layout = f"{fmt.engine} {fmt.level}"
    progress.stage(STAGE_CONTAMINANTS)
    if fmt.level == "long":
        contaminants = compute_contaminant_fraction_per_sample(
            raw,
            precursor_column=raw.attrs["precursor_id_column"],
            contaminant_prefixes=prefixes,
            contaminants_fasta=fasta,
        )
        progress.stage(STAGE_FILTERING)
        psm = filter_contaminants(raw, contaminants_fasta=fasta, prefix_patterns=prefixes)
        summary = ReportSummary(path, layout, UNIT_ROWS, len(raw), len(psm), _runs(psm))
        return LoadedReport(data=psm, contaminants=contaminants, summary=summary)

    contaminants = ap.proteome.contaminant_fraction(
        adata, contaminants_fasta=fasta, prefix_patterns=prefixes
    )
    progress.stage(STAGE_FILTERING)
    clean = ap.proteome.drop_contaminant_proteins(
        adata, contaminants_fasta=fasta, prefix_patterns=prefixes
    )
    runs = tuple(sorted(str(r) for r in clean.obs_names))
    summary = ReportSummary(path, layout, UNIT_PROTEIN_GROUPS, adata.n_vars, clean.n_vars, runs)
    return LoadedReport(data=clean, contaminants=contaminants, summary=summary)
