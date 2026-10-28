"""Report loading: the real reader on real-format fixtures, plus every error path."""

from __future__ import annotations

from pathlib import Path

import alphaphos as ap
import pandas as pd
import pytest

from alphaphos_gui.core import (
    PHOSPHO,
    Progress,
    ReportError,
    Session,
    clean_path,
    load_proteome_report,
    load_report,
)

# Trimmed Spectronaut EGF report from alphaPhos tests/data: 6 runs, 2162 rows,
# no contaminants.
EGF_MINI = Path(__file__).parent / "data" / "egf_mini.tsv"
SPIKED_ROWS = 40
PROTEOME_RUNS = ["DO018_proteome_A1", "DO018_proteome_A2"]


@pytest.fixture
def spiked_report(tmp_path) -> Path:
    """EGF fixture with the first rows relabelled as a CON__ contaminant protein."""
    df = pd.read_csv(EGF_MINI, sep="\t", low_memory=False)
    df.loc[: SPIKED_ROWS - 1, "PG.ProteinGroups"] = "CON__P02768"
    path = tmp_path / "spiked.tsv"
    df.to_csv(path, sep="\t", index=False)
    return path


def _write(path: Path, header: list[str], rows: list[list]) -> Path:
    lines = ["\t".join(header)] + ["\t".join(str(v) for v in r) for r in rows]
    # Bytes, so the CRLF line endings real exports use survive on every OS.
    path.write_bytes(("\r\n".join(lines) + "\r\n").encode())
    return path


@pytest.fixture(params=["spectronaut", "diann"])
def short_proteome(request, tmp_path) -> tuple[str, Path]:
    """A protein-level report in the header layout each engine really writes."""
    rows = [["P12345", "Gene1", 300.0, 100.0], ["Cont_P00761", "", 100.0, 300.0]]
    if request.param == "spectronaut":
        header = ["PG.ProteinGroups", "PG.Genes"] + [
            f"[{i}] {r}.raw.PG.Quantity" for i, r in enumerate(PROTEOME_RUNS, 1)
        ]
        return "Spectronaut short", _write(tmp_path / "proteome.tsv", header, rows)
    header = ["Protein.Group", "Genes"] + [f"V:\\raw\\{r}.raw" for r in PROTEOME_RUNS]
    return "DIA-NN short", _write(tmp_path / "report.pg_matrix.tsv", header, rows)


# ---- phospho ----


def test_session_loads_spectronaut_report():
    slot = Session()[PHOSPHO]
    report = slot.load(EGF_MINI)
    assert report.n_loaded == report.n_kept == 2162
    assert (report.layout, report.unit) == ("Spectronaut long", "rows")
    assert len(report.runs) == 6
    assert len(slot.loaded.data) == 2162
    assert slot.progress.state.state == "done"


def test_contaminants_measured_then_removed_like_the_reader(spiked_report):
    loaded = load_report(spiked_report)
    # Same rows as the reader's default (contaminant-dropping) read.
    pd.testing.assert_frame_equal(
        loaded.data.reset_index(drop=True), ap.read_spectronaut(spiked_report)
    )
    assert loaded.summary.n_loaded - loaded.summary.n_kept == SPIKED_ROWS
    frac = loaded.contaminants["contaminant_fraction"]
    assert len(frac) == 6 and (frac > 0).any() and (frac < 1).all()


def test_progress_reports_reading_then_named_stages():
    seen = []

    class Recording(Progress):
        def stage(self, name, fraction=None):
            seen.append((name, fraction))
            super().stage(name, fraction)

    load_report(EGF_MINI, Recording())
    reading = [f for name, f in seen if name == "Reading file"]
    assert reading[0] == 0.0 and reading == sorted(reading) and reading[-1] < 1.0
    # Once every byte is read, the remaining stages cannot measure themselves.
    later = [
        step for i, step in enumerate(seen[len(reading) :]) if seen[len(reading) + i - 1] != step
    ]
    assert later == [
        ("Parsing file", None),
        ("Measuring contaminants", None),
        ("Removing contaminants", None),
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (r'"D:\data\report.tsv"', Path(r"D:\data\report.tsv")),  # Windows "Copy as path"
        ("  /data/report.tsv \n", Path("/data/report.tsv")),
    ],
)
def test_clean_path(text, expected):
    assert clean_path(text) == expected


def test_load_errors_are_readable_and_keep_previous_report(tmp_path):
    slot = Session()[PHOSPHO]
    slot.load(EGF_MINI)

    not_a_report = tmp_path / "samples.tsv"
    not_a_report.write_text("a\tb\n1\t2\n")
    (tmp_path / "notes.docx").write_text("x")
    cases = {
        tmp_path / "missing.tsv": "No file at",
        tmp_path / "notes.docx": "not a report file",
        not_a_report: "Could not read samples.tsv",
    }
    for path, message in cases.items():
        with pytest.raises(ReportError, match=message):
            slot.load(path)
        assert slot.progress.state.state == "error"
        assert message in slot.progress.state.message
    assert slot.report.source.name == EGF_MINI.name


# ---- proteome ----


def test_short_proteome_measured_then_contaminants_removed(short_proteome):
    layout, path = short_proteome
    loaded = load_proteome_report(path)
    summary = loaded.summary
    assert (summary.layout, summary.unit) == (layout, "protein groups")
    assert (summary.n_loaded, summary.n_kept) == (2, 1)
    assert summary.runs == tuple(PROTEOME_RUNS)
    assert list(loaded.data.var_names) == ["P12345"]
    frac = loaded.contaminants["contaminant_fraction"].to_numpy()
    assert frac == pytest.approx([100 / 400, 300 / 400])


def test_diann_precursor_proteome_is_refused_with_a_hint(tmp_path):
    path = _write(tmp_path / "report.tsv", ["Run", "Protein.Group", "Precursor.Id"], [])
    with pytest.raises(ReportError, match="pg_matrix"):
        load_proteome_report(path)
