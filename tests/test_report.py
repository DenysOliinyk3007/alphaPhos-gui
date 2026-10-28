"""Report loading: the real reader on a real Spectronaut fixture, plus every error path."""

from __future__ import annotations

from pathlib import Path

import pytest

from alphaphos_gui.core import ReportError, Session, clean_path

# Trimmed Spectronaut EGF report from alphaPhos tests/data: 6 runs, 2162 rows.
EGF_MINI = Path(__file__).parent / "data" / "egf_mini.tsv"


def test_session_loads_spectronaut_report():
    session = Session()
    report = session.load(EGF_MINI)
    assert report.n_rows_loaded == report.n_rows_kept == 2162
    assert len(report.runs) == 6
    assert all("nanoPhos_dilser" in r for r in report.runs)
    assert session.psm is not None and len(session.psm) == 2162


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
    session = Session()
    session.load(EGF_MINI)

    not_a_report = tmp_path / "samples.tsv"
    not_a_report.write_text("a\tb\n1\t2\n")
    cases = {
        tmp_path / "missing.tsv": "No file at",
        tmp_path / "notes.docx": "not a report file",
        not_a_report: "Could not read samples.tsv",
    }
    (tmp_path / "notes.docx").write_text("x")
    for path, message in cases.items():
        with pytest.raises(ReportError, match=message):
            session.load(path)
    assert session.report is not None and session.report.source.name == EGF_MINI.name
