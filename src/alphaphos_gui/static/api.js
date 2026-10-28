// Shared helpers: JSON API calls, number formatting, and the lazily loaded plotly.js.

export const fmt = new Intl.NumberFormat();
export const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export async function api(path, options = {}) {
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

let plotlyReady = null;

// plotly.js (~5 MB) is served by the local server and fetched on first use only,
// once for every loader on the page.
export function loadPlotly() {
  plotlyReady ??= new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "/vendor/plotly.min.js";
    script.onload = () => resolve(window.Plotly);
    script.onerror = () => {
      plotlyReady = null;
      reject(new Error("Could not load the plotting library."));
    };
    document.head.append(script);
  });
  return plotlyReady;
}
