"""Progress of a long-running step, written by a worker thread and read by the server."""

from __future__ import annotations

import threading
from dataclasses import asdict, dataclass

IDLE, RUNNING, DONE, ERROR = "idle", "running", "done", "error"


@dataclass(frozen=True)
class ProgressState:
    state: str = IDLE
    stage: str = ""
    # 0..1 while a stage can measure itself; None while it can't (indeterminate).
    fraction: float | None = None
    message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class Progress:
    """Snapshot-style progress: each update replaces the whole state under a lock."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = ProgressState()

    @property
    def state(self) -> ProgressState:
        with self._lock:
            return self._state

    @property
    def running(self) -> bool:
        return self.state.state == RUNNING

    def stage(self, name: str, fraction: float | None = None) -> None:
        self._set(ProgressState(RUNNING, name, fraction))

    def done(self, message: str) -> None:
        self._set(ProgressState(DONE, "", 1.0, message))

    def error(self, message: str) -> None:
        self._set(ProgressState(ERROR, "", None, message))

    def _set(self, state: ProgressState) -> None:
        with self._lock:
            self._state = state
