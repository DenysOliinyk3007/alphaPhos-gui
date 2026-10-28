// One report loader: path entry, progress, summary, run list and contaminant plot.
// The same component serves the phospho and the proteome report; `config` says
// which API routes and labels to use.  Every value from the server is inserted
// with textContent, never as HTML.

import { api, fmt, loadPlotly, sleep } from "./api.js";

const POLL_MS = 200;
// Horizontal room one rotated tick label needs before labels start to overlap.
const MIN_TICK_PX = 18;
const COUNT_LABELS = {
  rows: ["Rows read", "Rows kept after filters"],
  "protein groups": ["Protein groups read", "Protein groups kept"],
};
const CONTAMINANT_HINTS = {
  rows: "% of each run's precursor intensity from contaminants, before removal.",
  "protein groups": "% of each run's protein intensity from contaminants, before removal.",
};

export function createLoader(root, config) {
  root.replaceChildren(document.getElementById("loader-template").content.cloneNode(true));
  const field = (name) => root.querySelector(`[data-field="${name}"]`);
  const base = `/api/${config.kind}`;

  field("step").textContent = String(config.step);
  field("title").textContent = config.title;
  field("optional").hidden = !config.optional;
  field("hint").textContent = config.hint;
  field("path").placeholder = config.placeholder;
  field("path").setAttribute("aria-label", `${config.title} path`);

  function showStatus(message, kind) {
    field("status").textContent = message;
    field("status").dataset.kind = kind;
    field("status").hidden = false;
  }

  // ---- progress ----

  function showProgress(state) {
    const track = field("track");
    const measurable = state.fraction !== null;
    track.classList.toggle("indeterminate", !measurable);
    if (measurable) {
      const percent = Math.round(state.fraction * 100);
      field("bar").style.width = `${percent}%`;
      track.setAttribute("aria-valuenow", String(percent));
      field("progress-label").textContent = `${state.stage || "Starting"} · ${percent}%`;
    } else {
      field("bar").style.width = "";
      track.removeAttribute("aria-valuenow");
      field("progress-label").textContent = `${state.stage || "Starting"}…`;
    }
    field("progress").hidden = false;
  }

  async function waitForLoad() {
    for (;;) {
      const state = await api(`${base}/report/progress`);
      if (state.state === "done" || state.state === "error") return state;
      showProgress(state);
      await sleep(POLL_MS);
    }
  }

  // ---- summary ----

  function renderSummary(report) {
    const [loadedLabel, keptLabel] = COUNT_LABELS[report.unit] ?? COUNT_LABELS.rows;
    field("name").textContent = report.name;
    field("source").textContent = `${report.layout} · ${report.source}`;
    field("source").title = report.source;
    field("loaded-label").textContent = loadedLabel;
    field("kept-label").textContent = keptLabel;
    field("n-loaded").textContent = fmt.format(report.n_loaded);
    field("n-kept").textContent = fmt.format(report.n_kept);
    field("n-runs").textContent = fmt.format(report.runs.length);
    field("contaminants-hint").textContent = CONTAMINANT_HINTS[report.unit] ?? CONTAMINANT_HINTS.rows;
    field("runs").replaceChildren(
      ...report.runs.map((run) => {
        const li = document.createElement("li");
        li.textContent = run;
        return li;
      }),
    );
    // A new report starts with the run list and the plot closed.
    setRunsOpen(false);
    closeContaminants();
    field("summary").hidden = false;
  }

  function setRunsOpen(open) {
    field("runs-panel").hidden = !open;
    field("toggle-runs").setAttribute("aria-expanded", String(open));
    field("toggle-runs").textContent = open ? "Hide runs" : "See all runs";
  }

  // ---- contaminant plot ----

  async function checkContaminants() {
    const button = field("check-contaminants");
    button.disabled = true;
    try {
      const [Plotly, figure] = await Promise.all([loadPlotly(), api(`${base}/qc/contaminants`)]);
      // Shown before plotting: Plotly sizes to its container, and a hidden one is 0 px wide.
      field("contaminants-panel").hidden = false;
      // On screen the figure fits its card (and follows window resizes); the
      // fixed publication width from ap.viz is for exported figures.
      const layout = { ...figure.layout, width: undefined, autosize: true };
      // Fitted to a card, many runs leave no room for their names; drop the
      // tick labels then and point to the hover, which shows each full name.
      const runs = figure.data[0]?.x?.length ?? 0;
      if (runs * MIN_TICK_PX > field("contaminants-plot").clientWidth) {
        layout.xaxis = {
          ...layout.xaxis,
          showticklabels: false,
          title: { ...layout.xaxis?.title, text: `${runs} runs · hover a bar for its name` },
        };
      }
      await Plotly.newPlot(field("contaminants-plot"), figure.data, layout, {
        displaylogo: false,
        responsive: true,
      });
      button.setAttribute("aria-pressed", "true");
      field("contaminants-panel").scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (error) {
      showStatus(error.message, "error");
    } finally {
      button.disabled = false;
    }
  }

  function closeContaminants() {
    if (window.Plotly) window.Plotly.purge(field("contaminants-plot"));
    field("contaminants-panel").hidden = true;
    field("check-contaminants").setAttribute("aria-pressed", "false");
  }

  // ---- load ----

  async function loadReport(event) {
    event.preventDefault();
    const path = field("path").value;
    if (!path.trim()) {
      showStatus("Enter the path to a report first.", "warn");
      return;
    }
    try {
      showProgress(await api(`${base}/report`, { method: "POST", body: JSON.stringify({ path }) }));
    } catch (error) {
      showStatus(error.message, "error");
      return;
    }
    await followLoad();
  }

  // Shows progress until the server's load job ends, then the result.
  async function followLoad() {
    const button = field("load");
    button.disabled = true;
    field("status").hidden = true;
    try {
      const result = await waitForLoad();
      if (result.state === "error") {
        // The previous report, if any, stays on screen.
        showStatus(result.message, "error");
        return;
      }
      renderSummary(await api(`${base}/report`));
      showStatus(result.message, "ok");
    } catch (error) {
      showStatus(error.message, "error");
    } finally {
      field("progress").hidden = true;
      button.disabled = false;
    }
  }

  field("form").addEventListener("submit", loadReport);
  field("toggle-runs").addEventListener("click", () => setRunsOpen(field("runs-panel").hidden));
  field("check-contaminants").addEventListener("click", checkContaminants);
  field("close-contaminants").addEventListener("click", closeContaminants);

  // The server keeps the session, so a page reload restores the last report,
  // or picks up a load that is still running.
  async function restore() {
    const report = await api(`${base}/report`);
    if (report) renderSummary(report);
    const progress = await api(`${base}/report/progress`);
    if (progress.state === "running") {
      showProgress(progress);
      await followLoad();
    }
  }
  restore().catch((error) => showStatus(error.message, "error"));
}
