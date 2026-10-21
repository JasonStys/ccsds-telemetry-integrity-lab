/** Local capture-inspection controller by Jason Stys.
 * Functions: settings, inspect, renderLedger, render, loadCapture, preference handlers.
 * Variables: current evidence, selected row, request generation and AbortController.
 * Exact declarations/DOM IDs: docs/CODE_INDEX.md. No implicit persistence or external fetch.
 */
import "./style.css";
import {
  defaults,
  escapeText as esc,
  query,
  readPreferences,
  headerMarkup,
  type Settings,
  type Evidence,
} from "./contracts";

/** Resolve static template IDs with explicit failure on an authoring contract mismatch. */
function element<T extends HTMLElement>(id: string): T {
  const node = document.getElementById(id);
  if (!node) throw new Error("Missing UI element");
  return node as T;
}
let current: Evidence | null = null;
let selected = 0;
let generation = 0;
let pending: AbortController | null = null;
const key = "telemetry-integrity-controls-v1";
const remember = element<HTMLInputElement>("remember");
const status = element("status");

/** Read the three finite native/browser control values from reviewed selects. */
function settings(): Settings {
  return {
    scenario: element<HTMLSelectElement>("scenario").value,
    payload_limit: Number(element<HTMLSelectElement>("payload_limit").value),
    forward_window: Number(element<HTMLSelectElement>("forward_window").value),
  };
}

/** Persist only explicit optional controls, not packets or user data; failure is nonfatal. */
function savePreferences(): void {
  try {
    if (remember.checked) localStorage.setItem(key, JSON.stringify(settings()));
    else localStorage.removeItem(key);
  } catch {
    status.textContent =
      "Browser storage unavailable. Inspection still works; controls are not saved.";
  }
}

/** Restore validated controls or defaults; inaccessible/malformed storage never blocks inspection. */
function restorePreferences(): void {
  let value: Settings | null = null;
  try {
    value = readPreferences(localStorage.getItem(key));
  } catch {
    /* Optional browser storage may be blocked. */
  }
  remember.checked = value !== null;
  for (const [name, setting] of Object.entries(value ?? defaults))
    element<HTMLSelectElement>(name).value = String(setting);
}

/** Decode no mission-specific fields; present native header, bounds and opaque bytes explicitly. */
function inspect(): void {
  const row = current?.rows[selected];
  element("selected-record").textContent = row ? `Record ${row.index + 1}` : "Empty capture";
  if (!row) {
    element("inspection").textContent =
      "No records supplied. This is a valid empty capture, not parser success on an unseen packet.";
    return;
  }
  const h = row.header;
  const facts = h
    ? [
        ["Version / type", `${h.version} / ${h.packet_type}`],
        ["Secondary / flags", `${h.secondary} / ${h.flags}`],
        ["APID", h.apid],
        ["Sequence count", h.sequence],
        ["Encoded data length", h.data_length],
        ["Data bytes declared", h.data_length + 1],
        ["Actual / expected bytes", `${row.actual_size} / ${h.expected_size}`],
        ["Baseline advanced", row.baseline_advanced ? "Yes" : "No"],
      ]
    : [
        ["Actual bytes", row.actual_size ?? "Undecodable hex"],
        ["Primary header", "Unavailable"],
      ];
  element("inspection").innerHTML =
    `<div class="inspector-status"><strong class="${row.code === "accepted" ? "ok-text" : "bad-text"}">${esc(row.code)}</strong><span>${esc(row.disposition.replaceAll("-", " "))}</span></div><div class="bit-scroll" tabindex="0" role="region" aria-label="Scrollable primary header">${headerMarkup(row.raw_hex)}</div><dl class="facts">${facts.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl><div class="byte-box"><p>RAW RECORD / HEX OR INVALID INPUT</p><pre>${esc(row.raw_hex.slice(0, 256))}${row.raw_hex.length > 256 ? "… (full record in JSON)" : ""}</pre></div><div class="byte-box"><p>OPAQUE PAYLOAD / HEX</p><pre>${esc(row.payload_hex.slice(0, 256) || "No accepted payload exposed")}${row.payload_hex.length > 256 ? "… (full payload in JSON)" : ""}</pre></div><p class="inspection-note">${row.unobserved_values ? `${esc(row.unobserved_values)} sequence values were not observed between accepted baselines. This is not proof of permanent loss. ` : ""}No embedded payload checksum or sender authentication is verified. Payload meaning, timestamps and units are not inferred.</p>`;
}

/** Filter drawing only; complete capture metrics, evidence and selected-record detail remain explicit. */
function renderLedger(): void {
  if (!current) return;
  const filter = element<HTMLSelectElement>("record-filter").value;
  const rows = current.rows.filter(
    (row) =>
      filter === "all" ||
      (filter === "review"
        ? row.review
        : filter === "accepted"
          ? row.code === "accepted"
          : row.code !== "accepted"),
  );
  element("records").innerHTML = rows
    .map(
      (row) =>
        `<tr${row.index === selected ? ' class="selected"' : ""}><th scope="row"><button type="button" data-record="${esc(row.index)}" aria-label="Inspect record ${esc(row.index + 1)}">${esc(String(row.index + 1).padStart(2, "0"))} <span aria-hidden="true">↗</span></button></th><td>${esc(row.header?.apid ?? "—")} <span>${esc(row.header?.sequence ?? "No header")}</span></td><td class="mono">${esc(row.actual_size ?? "?")} / ${esc(row.header?.expected_size ?? "?")}</td><td><span class="outcome ${row.code !== "accepted" ? "rejected" : row.review ? "review" : "accepted"}">${esc(row.code === "accepted" ? (row.review ? "Review" : row.disposition === "idle" ? "Idle" : "Accepted") : "Rejected")}</span></td><td>${esc(row.code === "accepted" ? row.disposition.replaceAll("-", " ") : row.code.replaceAll("-", " "))}${row.unobserved_values ? `<span>${esc(row.unobserved_values)} unobserved values</span>` : ""}</td></tr>`,
    )
    .join("");
  element("empty").hidden = rows.length > 0;
}

/** Render fully escaped complete evidence; downloads are fixed same-origin attachment routes. */
function render(run: Evidence): void {
  const t = run.totals;
  element("metrics").innerHTML = [
    ["STRUCTURALLY ACCEPTED", t.accepted, "Includes idle and review records"],
    ["REJECTED", t.rejected, "Profile or structure mismatch"],
    ["CONTINUITY REVIEW", t.review, "Not an automatic discard"],
    ["REFERENCE AGREEMENT", `${t.records}/${t.records}`, "Rust ↔ independent Python"],
  ]
    .map(
      ([label, value, note]) =>
        `<article><p>${esc(label)}</p><strong>${esc(value)}</strong><span>${esc(note)}</span></article>`,
    )
    .join("");
  element("agreement").textContent = `${t.records} / ${t.records} parser agreement`;
  element("scenario-note").textContent = run.note;
  element("evidence-id").textContent =
    `REPORT SHA-256 / ${run.id} · content identifier, not a signature`;
  element("downloads").innerHTML = [
    ["json", "Full JSON"],
    ["csv", "Record CSV"],
    ["html", "HTML report"],
    ["input", "Input capture"],
  ]
    .map(
      ([format, label]) =>
        `<a download href="/api/report?${esc(query(settings()))}&amp;format=${format}">${label} ↓</a>`,
    )
    .join("");
  renderLedger();
  inspect();
}

/** Abort obsolete requests, hide stale evidence and withhold results if either parser fails. */
async function loadCapture(): Promise<void> {
  pending?.abort();
  pending = new AbortController();
  const token = ++generation;
  element("results").hidden = true;
  element("error").hidden = true;
  element<HTMLButtonElement>("run-button").disabled = true;
  status.textContent = "Running Rust inspection and independent Python comparison…";
  try {
    const response = await fetch(`/api/run?${query(settings())}`, {
      signal: pending.signal,
      credentials: "omit",
    });
    if (!response.ok) throw new Error("Inspection unavailable");
    const evidence = (await response.json()) as Evidence;
    if (token !== generation) return;
    current = evidence;
    selected = 0;
    render(evidence);
    element("results").hidden = false;
    status.textContent = `Inspection complete. ${evidence.totals.records} records; ${evidence.totals.rejected} rejected; ${evidence.totals.review} for continuity review.`;
    if (remember.checked) savePreferences();
  } catch (error) {
    if (token !== generation || (error instanceof DOMException && error.name === "AbortError"))
      return;
    current = null;
    element("error").hidden = false;
    status.textContent = "Inspection unavailable. No evidence is being shown.";
  } finally {
    if (token === generation) element<HTMLButtonElement>("run-button").disabled = false;
  }
}

element<HTMLFormElement>("controls").addEventListener("submit", (event) => {
  event.preventDefault();
  void loadCapture();
});
element("controls").addEventListener("change", () => {
  pending?.abort();
  generation++;
  element("results").hidden = true;
  element<HTMLButtonElement>("run-button").disabled = false;
  status.textContent = "Controls changed. Inspect again to refresh all evidence and downloads.";
});
element("retry").addEventListener("click", () => {
  void loadCapture();
});
element("record-filter").addEventListener("change", renderLedger);
element("records").addEventListener("click", (event) => {
  const button =
    event.target instanceof Element
      ? event.target.closest<HTMLButtonElement>("button[data-record]")
      : null;
  if (button) {
    selected = Number(button.dataset.record);
    renderLedger();
    inspect();
  }
});
remember.addEventListener("change", savePreferences);
restorePreferences();
void loadCapture();
