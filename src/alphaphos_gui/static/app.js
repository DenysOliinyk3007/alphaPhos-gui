// Page logic: talks to the local server's JSON API and renders the results.
// Every value from the server is inserted with textContent, never as HTML, so
// file names and run names cannot inject markup.

const $ = (id) => document.getElementById(id);
const fmt = new Intl.NumberFormat();

function showStatus(message, kind) {
  const status = $("status");
  status.textContent = message;
  status.dataset.kind = kind;
  status.hidden = false;
}

function renderSummary(report) {
  $("summary-title").textContent = report.name;
  $("summary-source").textContent = report.source;
  $("rows-loaded").textContent = fmt.format(report.n_rows_loaded);
  $("rows-kept").textContent = fmt.format(report.n_rows_kept);
  $("n-runs").textContent = fmt.format(report.runs.length);
  $("runs").replaceChildren(
    ...report.runs.map((run) => {
      const li = document.createElement("li");
      li.textContent = run;
      return li;
    }),
  );
  $("summary").hidden = false;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    // FastAPI puts the message in "detail"; validation errors give a list.
    const detail = body?.detail;
    throw new Error(typeof detail === "string" ? detail : `Request failed (${response.status}).`);
  }
  return body;
}

async function loadReport(event) {
  event.preventDefault();
  const path = $("path").value;
  if (!path.trim()) {
    showStatus("Enter the path to a report first.", "warn");
    return;
  }
  const button = $("load");
  button.disabled = true;
  showStatus("Reading report…", "busy");
  try {
    const report = await api("/api/report", {
      method: "POST",
      body: JSON.stringify({ path }),
    });
    renderSummary(report);
    showStatus(`Loaded ${report.name}.`, "ok");
  } catch (error) {
    // The previous report, if any, stays on screen.
    showStatus(error.message, "error");
  } finally {
    button.disabled = false;
  }
}

async function init() {
  $("load-form").addEventListener("submit", loadReport);
  const info = await api("/api/info");
  $("version").textContent = `GUI ${info.version} · alphaPhos ${info.alphaphos_version}`;
  // The server keeps the session, so a page reload restores the last report.
  const report = await api("/api/report");
  if (report) renderSummary(report);
}

init().catch((error) => showStatus(error.message, "error"));
