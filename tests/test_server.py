"""HTTP API and page serving, through FastAPI's test client and the real reader."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from alphaphos_gui.core import Session
from alphaphos_gui.server import create_app

EGF_MINI = Path(__file__).parent / "data" / "egf_mini.tsv"


@pytest.fixture
def client():
    return TestClient(create_app(), base_url="http://localhost:5006")


def load(client, path) -> dict:
    """Start a background load and poll it to the end, as the page does."""
    started = client.post("/api/phospho/report", json={"path": str(path)})
    assert started.status_code == 202, started.text
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        state = client.get("/api/phospho/report/progress").json()
        if state["state"] in ("done", "error"):
            return state
        time.sleep(0.05)
    raise AssertionError("load did not finish")


def test_page_and_assets_are_served(client):
    page = client.get("/")
    assert page.status_code == 200 and "<title>alphaPhos</title>" in page.text
    for asset in ("/static/app.js", "/static/style.css", "/vendor/plotly.min.js"):
        assert client.get(asset).status_code == 200, asset


def test_load_report_then_restore_it(client):
    assert client.get("/api/phospho/report").json() is None

    state = load(client, f'"{EGF_MINI}"')
    assert state["state"] == "done" and "egf_mini.tsv" in state["message"]
    body = client.get("/api/phospho/report").json()
    assert body["n_loaded"] == body["n_kept"] == 2162 and body["unit"] == "rows"
    assert len(body["runs"]) == 6


def test_load_errors_end_the_job_with_a_message(client):
    assert client.post("/api/phospho/report", json={"path": "   "}).status_code == 400
    state = load(client, "D:/nope/missing.tsv")
    assert state["state"] == "error" and "No file at" in state["message"]


def test_second_load_while_running_is_refused():
    session = Session()
    session["phospho"].progress.stage("Reading file", 0.3)  # a load in flight
    client = TestClient(create_app(session), base_url="http://localhost:5006")
    response = client.post("/api/phospho/report", json={"path": str(EGF_MINI)})
    assert response.status_code == 409 and "already loading" in response.json()["detail"]


def test_contaminant_figure(client):
    assert client.get("/api/phospho/qc/contaminants").status_code == 404  # nothing loaded yet
    load(client, EGF_MINI)
    figure = client.get("/api/phospho/qc/contaminants").json()
    (bars,) = figure["data"]
    assert bars["type"] == "bar" and len(bars["x"]) == 6
    assert figure["layout"]["height"] == 600


def test_requests_from_other_sites_are_refused(client):
    # Another website open in the same browser cannot drive the local API...
    foreign = client.post(
        "/api/phospho/report",
        json={"path": str(EGF_MINI)},
        headers={"Origin": "https://evil.example"},
    )
    assert foreign.status_code == 403
    # ...nor reach it through a rebound DNS name.
    rebound = TestClient(create_app(), base_url="http://evil.example:5006")
    assert rebound.get("/api/phospho/report").status_code == 400
    # The page's own origin is accepted.
    own = client.post(
        "/api/phospho/report",
        json={"path": str(EGF_MINI)},
        headers={"Origin": "http://localhost:5006"},
    )
    assert own.status_code == 202


def test_phospho_and_proteome_slots_are_independent(client):
    load(client, EGF_MINI)
    assert client.get("/api/proteome/report").json() is None
    assert client.get("/api/proteome/report/progress").json()["state"] == "idle"
    assert client.get("/api/proteome/qc/contaminants").status_code == 404
    assert client.get("/api/lipidome/report").status_code == 404
