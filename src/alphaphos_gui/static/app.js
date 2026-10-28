// Page shell: tabs, version line, and the two report loaders.

import { api } from "./api.js";
import { createLoader } from "./loader.js";

const LOADERS = [
  {
    kind: "phospho",
    step: 1,
    title: "Phospho report",
    optional: false,
    hint: 'Paste the path to a Spectronaut report (.tsv, .txt or .parquet). "Copy as path" from Explorer works as-is.',
    placeholder: "D:\\data\\phospho_report.tsv",
  },
  {
    kind: "proteome",
    step: 2,
    title: "Proteome report",
    optional: true,
    hint: "Spectronaut or DIA-NN (e.g. report.pg_matrix.tsv). Protein-level or precursor-level is detected from the file.",
    placeholder: "D:\\data\\proteome_report.tsv",
  },
];

function showTab(id) {
  for (const tab of document.querySelectorAll('[role="tab"]')) {
    const selected = tab.id === id;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    document.getElementById(tab.getAttribute("aria-controls")).hidden = !selected;
  }
}

function initTabs() {
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  for (const tab of tabs) tab.addEventListener("click", () => showTab(tab.id));
  // Arrow keys move between tabs, as the ARIA tab pattern expects.
  document.querySelector('[role="tablist"]').addEventListener("keydown", (event) => {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (!step) return;
    const next = tabs[(tabs.indexOf(document.activeElement) + step + tabs.length) % tabs.length];
    next.focus();
    showTab(next.id);
  });
}

initTabs();
for (const config of LOADERS) createLoader(document.getElementById(`loader-${config.kind}`), config);
api("/api/info").then(
  (info) => {
    document.getElementById("version").textContent =
      `GUI ${info.version} · alphaPhos ${info.alphaphos_version}`;
  },
  () => {},
);
