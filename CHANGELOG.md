# Changelog

All notable changes to alphaphos-gui are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Needs alphaPhos with `read_spectronaut(progress=...)`, `ap.viz.contaminant_fraction`,
`ap.proteome.detect_report_format` / `read_diann_pg_matrix` / `contaminant_fraction`
and the fixed QC column defaults (alphaPhos branch `qc-for-gui`, after 0.25.0).

### Added

- **Progress bar while a report loads.** Loading runs as a background job the
  page polls. Reading shows a real percentage (bytes read); the stages that
  cannot measure themselves (parsing, measuring and removing contaminants) show
  their name with a moving bar. Reloading the page mid-load picks the progress
  back up.
- **"Check contaminants"**: a bar plot of the % of each run's precursor
  intensity from contaminant proteins (`ap.viz.contaminant_fraction`), opened
  inside the report card with a close button. Wide figures keep their
  publication width and scroll inside the card. plotly.js is served from the
  installed plotly package, so it works offline.
- **"See all runs"** toggles the run list, which is now hidden by default.
- **Proteome report loader**, side by side with the phospho one on a new
  **Data** tab (stacked on narrow windows). Same content: path, progress,
  counts, runs, contaminant plot. The format is detected from the header:
  Spectronaut short, DIA-NN `report.pg_matrix.tsv`, or Spectronaut long;
  DIA-NN precursor-level reports are refused with a pointer to the pg_matrix.
  Protein-level reports count protein groups instead of rows; contaminant
  protein groups are measured, then removed. The two loaders are independent
  and can run at the same time. Side by side, the two columns share row heights,
  so both cards and both path fields stay aligned whichever text wraps.
- **Conditions** tab (placeholder for the condition builder).

### Changed

- The report is read once with contaminants kept, so they can be measured, then
  filtered with alphaPhos's own contaminant filter and reader settings. The
  result is identical to `read_spectronaut`'s default output (tested).
- A second load while one is running is refused with a message.
- On screen, plots are drawn at their card's width (and follow window
  resizes) instead of `ap.viz`'s fixed publication width; when there are too
  many runs to name at that width, the axis says "N runs · hover a bar for its
  name". Long source paths stay on one line (full path on hover).
- API routes carry the report kind: `/api/{phospho|proteome}/report`,
  `.../report/progress`, `.../qc/contaminants`.

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
