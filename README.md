# alphaphos-gui

Local browser GUI for [alphaPhos](https://github.com/DenysOliinyk3007/alphaPhos)
phosphoproteomics analysis. It runs on your own machine: the app opens in your
browser, and your data stays on your disk.

**Status:** pre-alpha (v0.1.0). It can load a Spectronaut report and show what was
read. Sample annotation, site collapse, QC and export come next.

## Install

```bash
pip install "alphaphos-gui @ git+https://github.com/DenysOliinyk3007/alphaphos-gui.git"
```

This also installs alphaPhos (from its GitHub `main` branch), FastAPI and uvicorn.

## Run

```bash
alphaphos-gui
```

A browser tab opens at `http://127.0.0.1:5006`. Paste the path to a Spectronaut
report (`.tsv`, `.txt` or `.parquet`) and press **Load report**. Windows
"Copy as path" works as-is; the quotes are stripped.

Options: `--port 5010` to use another port, `--no-browser` to start the server
without opening a tab.

**"'alphaphos-gui' is not recognized"** means the environment it was installed
into is not active. Activate it first, or run it by full path
(`<env>\Scripts\alphaphos-gui.exe`). To make it work in every Command Prompt,
put a one-line launcher `alphaphos-gui.cmd` in a folder that is on your PATH:

```bat
@"<env>\Scripts\alphaphos-gui.exe" %*
```

## Design

- **No science code in the GUI.** Every analysis step is one public `alphaphos`
  call. A bug in an analysis step is fixed in alphaPhos, not here.
- **Three layers.** `alphaphos_gui.core` holds the session state and logic
  with no web dependency, tested with plain pytest. `alphaphos_gui.server`
  (FastAPI) exposes it as a small JSON API. The page in
  `src/alphaphos_gui/static/` is plain HTML/CSS/JS with no build step, so it
  ships inside the wheel.
- **Local only.** The server listens on `127.0.0.1` and refuses requests whose
  `Host` or `Origin` is not localhost, so other websites open in your browser
  cannot use it to read your files.

## Develop

```bash
git clone https://github.com/DenysOliinyk3007/alphaphos-gui.git
cd alphaphos-gui
pip install -e ".[dev]"
ruff check src tests && ruff format --check src tests
pytest
```

When alphaPhos is already installed in editable mode, use
`pip install -e . --no-deps` so pip does not replace it with the GitHub version.

## License

MIT — see [LICENSE](LICENSE).
