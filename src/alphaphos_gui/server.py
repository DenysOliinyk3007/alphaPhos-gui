"""HTTP layer: serves the static page and a JSON API over :class:`~alphaphos_gui.core.Session`.

Holds no logic beyond translating requests to ``core`` calls and errors to
HTTP responses.
"""

from __future__ import annotations

import contextlib
import threading
from pathlib import Path
from urllib.parse import urlsplit

import alphaphos as ap
import plotly
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.trustedhost import TrustedHostMiddleware

from alphaphos_gui._version import __version__
from alphaphos_gui.constants import (
    APP_TITLE,
    BUSY,
    EMPTY_PATH,
    FOREIGN_ORIGIN,
    LOCAL_HOSTS,
    UNKNOWN_KIND,
)
from alphaphos_gui.core import ReportError, ReportSlot, ReportSummary, Session, clean_path

STATIC_DIR = Path(__file__).parent / "static"
# plotly.js as bundled with the installed plotly package: works offline and
# always matches the version that built the figure JSON.
PLOTLY_JS = Path(plotly.__file__).parent / "package_data" / "plotly.min.js"


class ReportRequest(BaseModel):
    path: str


def _summary_json(report: ReportSummary) -> dict:
    return {
        "name": report.source.name,
        "source": str(report.source),
        "layout": report.layout,
        "unit": report.unit,
        "n_loaded": report.n_loaded,
        "n_kept": report.n_kept,
        "runs": list(report.runs),
    }


def create_app(session: Session | None = None) -> FastAPI:
    """One local single-user app; the session lives as long as the server."""
    session = session or Session()
    start_lock = threading.Lock()
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

    def slot(kind: str) -> ReportSlot:
        if kind not in session.slots:
            raise HTTPException(status_code=404, detail=UNKNOWN_KIND.format(kind=kind))
        return session[kind]

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/vendor/plotly.min.js")
    def plotly_js() -> FileResponse:
        return FileResponse(PLOTLY_JS, media_type="text/javascript")

    @app.get("/api/info")
    def info() -> dict:
        return {"version": __version__, "alphaphos_version": ap.__version__}

    @app.get("/api/{kind}/report")
    def current_report(kind: str) -> dict | None:
        report = slot(kind).report
        return None if report is None else _summary_json(report)

    @app.post("/api/{kind}/report", status_code=202)
    def start_loading(kind: str, body: ReportRequest) -> dict:
        """Start reading in a background thread; the page polls the progress route."""
        target = slot(kind)
        if not body.path.strip():
            raise HTTPException(status_code=400, detail=EMPTY_PATH)
        path = clean_path(body.path)
        with start_lock:
            if target.progress.running:
                raise HTTPException(status_code=409, detail=BUSY)
            target.progress.stage("")  # mark running before the thread starts

            def run() -> None:
                # Failures are recorded in the slot's progress for the page to show.
                with contextlib.suppress(Exception):
                    target.load(path)

            threading.Thread(target=run, daemon=True).start()
        return target.progress.state.to_dict()

    @app.get("/api/{kind}/report/progress")
    def loading_progress(kind: str) -> dict:
        return slot(kind).progress.state.to_dict()

    @app.get("/api/{kind}/qc/contaminants")
    def contaminant_figure(kind: str) -> Response:
        try:
            figure = slot(kind).contaminant_figure()
        except ReportError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return Response(figure.to_json(), media_type="application/json")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app
