# Changelog

All notable changes to alphaphos-gui are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-28

### Added

- `alphaphos-gui` command: starts a local FastAPI server on `127.0.0.1` and
  opens the app in the browser; `--port` and `--no-browser` options.
- Plain HTML/CSS/JS front end (no build step), light and dark theme; a page
  reload restores the loaded report from the server session.
- Requests with a non-localhost `Host` or `Origin` are refused, so other
  websites cannot drive the local API.
- Load a Spectronaut report (`.tsv`, `.txt`, `.parquet`) by pasting its path.
  Quotes from Windows "Copy as path" are stripped. The report is read in a worker
  thread, so the server stays responsive on large files.
- Report summary: rows read, rows kept after the reader's filters, and the runs
  found.
- Readable errors for a missing file, a non-report file type, or a file that is
  not a Spectronaut report; a failed load keeps the previous report.
