"""``alphaphos-gui`` command: start the local server and open the browser."""

from __future__ import annotations

import argparse
import threading
import webbrowser

import uvicorn

from alphaphos_gui.constants import DEFAULT_PORT, HOST
from alphaphos_gui.server import create_app


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="alphaphos-gui", description="Start the alphaPhos GUI.")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"local port (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="start the server without opening a browser tab"
    )
    args = parser.parse_args(argv)

    # 127.0.0.1, not "localhost": on Windows localhost tries IPv6 ::1 first, which
    # the server does not listen on, and some clients wait for that to time out.
    url = f"http://{HOST}:{args.port}/"
    if not args.no_browser:
        # Opened just after startup; uvicorn.run blocks until the server stops.
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    print(f"alphaPhos GUI running at {url}  (Ctrl+C to stop)", flush=True)
    # Bound to the loopback interface only: the app reads files from this machine.
    uvicorn.run(create_app(), host=HOST, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
