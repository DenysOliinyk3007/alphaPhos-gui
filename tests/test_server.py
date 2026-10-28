"""HTTP API and page serving, through FastAPI's test client and the real reader."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from alphaphos_gui.server import create_app

EGF_MINI = Path(__file__).parent / "data" / "egf_mini.tsv"


@pytest.fixture
def client():
    return TestClient(create_app(), base_url="http://localhost:5006")


def test_page_and_assets_are_served(client):
    page = client.get("/")
    assert page.status_code == 200 and "<title>alphaPhos</title>" in page.text
    for asset in ("/static/app.js", "/static/style.css"):
        assert client.get(asset).status_code == 200


def test_load_report_then_restore_it(client):
    assert client.get("/api/report").json() is None

    loaded = client.post("/api/report", json={"path": f'"{EGF_MINI}"'})
    assert loaded.status_code == 200
    body = loaded.json()
    assert body["name"] == "egf_mini.tsv"
    assert body["n_rows_loaded"] == body["n_rows_kept"] == 2162
    assert len(body["runs"]) == 6

    # A page reload asks for the current report and gets the same one back.
    assert client.get("/api/report").json() == body


@pytest.mark.parametrize(
    ("path", "message"),
    [("   ", "Enter the path"), ("D:/nope/missing.tsv", "No file at")],
)
def test_load_errors_are_400_with_message(client, path, message):
    response = client.post("/api/report", json={"path": path})
    assert response.status_code == 400 and message in response.json()["detail"]


def test_requests_from_other_sites_are_refused(client):
    # Another website open in the same browser cannot drive the local API...
    foreign = client.post(
        "/api/report", json={"path": str(EGF_MINI)}, headers={"Origin": "https://evil.example"}
    )
    assert foreign.status_code == 403
    # ...nor reach it through a rebound DNS name.
    rebound = TestClient(create_app(), base_url="http://evil.example:5006")
    assert rebound.get("/api/report").status_code == 400
    # The page's own origin is accepted.
    own = client.post(
        "/api/report", json={"path": str(EGF_MINI)}, headers={"Origin": "http://localhost:5006"}
    )
    assert own.status_code == 200
