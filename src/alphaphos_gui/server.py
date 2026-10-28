"""HTTP layer: serves the static page and a JSON API over :class:`~alphaphos_gui.core.Session`.

Holds no logic beyond translating requests to ``core`` calls and errors to
HTTP responses.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

import alphaphos as ap
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.trustedhost import TrustedHostMiddleware

from alphaphos_gui._version import __version__
from alphaphos_gui.constants import APP_TITLE, EMPTY_PATH, FOREIGN_ORIGIN, LOCAL_HOSTS
from alphaphos_gui.core import ReportError, ReportSummary, Session, clean_path

STATIC_DIR = Path(__file__).parent / "static"


class ReportRequest(BaseModel):
    path: str


def _summary_json(report: ReportSummary) -> dict:
    return {
        "name": report.source.name,
        "source": str(report.source),
        "n_rows_loaded": report.n_rows_loaded,
        "n_rows_kept": report.n_rows_kept,
        "runs": list(report.runs),
    }


def create_app(session: Session | None = None) -> FastAPI:
    """One local single-user app; the session lives as long as the server."""
    session = session or Session()
    app = FastAPI(title=APP_TITLE, docs_url=None, redoc_url=None, openapi_url=None)

    # The API opens any path on this machine.  A Host check blocks DNS
    # rebinding; an Origin check blocks other websites open in the same
    # browser from sending requests to localhost.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(LOCAL_HOSTS))

    @app.middleware("http")
    async def same_origin_only(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin is not None and urlsplit(origin).hostname not in LOCAL_HOSTS:
            return JSONResponse({"detail": FOREIGN_ORIGIN}, status_code=403)
        return await call_next(request)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/info")
    def info() -> dict:
        return {"version": __version__, "alphaphos_version": ap.__version__}

    @app.get("/api/report")
    def current_report() -> dict | None:
        return None if session.report is None else _summary_json(session.report)

    # A plain ``def`` endpoint runs in FastAPI's thread pool, so a long read
    # does not block the server.
    @app.post("/api/report")
    def load_report(body: ReportRequest) -> dict:
        if not body.path.strip():
            raise HTTPException(status_code=400, detail=EMPTY_PATH)
        try:
            report = session.load(clean_path(body.path))
        except ReportError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _summary_json(report)

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app
