/** Typed evidence, finite preferences and inert byte graphics by Jason Stys.
 * Functions: escapeText, readPreferences, query, headerMarkup. Variables/types: Settings,
 * Header, RecordInfo, Evidence and profile controls. Exact lines: docs/CODE_INDEX.md.
 */
export interface Settings {
  scenario: string;
  payload_limit: number;
  forward_window: number;
}
export const defaults: Settings = { scenario: "nominal", payload_limit: 128, forward_window: 256 };
export const scenarios = [
  "nominal",
  "sequence-gap",
  "wraparound",
  "duplicate-and-reuse",
  "out-of-order",
  "ambiguous-jump",
  "truncated-and-length",
  "unsupported-profile",
  "payload-limit",
  "payload-corruption",
  "idle-and-recovery",
  "empty-capture",
];
export const choices = { payload_limit: [32, 128, 4096], forward_window: [16, 256, 8191] };
export interface Header {
  version: number;
  packet_type: number;
  secondary: number;
  apid: number;
  flags: number;
  sequence: number;
  data_length: number;
  expected_size: number;
}
export interface RecordInfo {
  index: number;
  raw_hex: string;
  code: string;
  header: Header | null;
  actual_size: number | null;
  payload_hex: string;
  disposition: string;
  unobserved_values: number;
  baseline_advanced: boolean;
  review: boolean;
  record_sha256: string;
}
export interface Evidence {
  id: string;
  scenario: string;
  settings: { payload_limit: number; forward_window: number };
  rows: RecordInfo[];
  totals: {
    records: number;
    accepted: number;
    rejected: number;
    review: number;
    idle: number;
    unobserved_values: number;
  };
  note: string;
}

/** Escape every dynamic text/attribute value, including fields normally guaranteed numeric. */
export function escapeText(value: unknown): string {
  return String(value).replace(
    /[&<>"']/g,
    (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]!,
  );
}

/** Restore only a complete finite control object; prototype names/coercion cannot widen options. */
export function readPreferences(raw: string | null): Settings | null {
  if (!raw || raw.length > 512) return null;
  try {
    const obj: unknown = JSON.parse(raw);
    if (!obj || typeof obj !== "object" || Array.isArray(obj)) return null;
    const value = obj as Record<string, unknown>;
    if (
      Object.keys(value).length !== 3 ||
      !Object.hasOwn(value, "scenario") ||
      !scenarios.includes(String(value.scenario))
    )
      return null;
    for (const [key, allowed] of Object.entries(choices))
      if (!Object.hasOwn(value, key) || !(allowed as unknown[]).includes(value[key])) return null;
    return value as unknown as Settings;
  } catch {
    return null;
  }
}

/** Encode only current finite controls; no arbitrary service URLs or filesystem paths. */
export function query(settings: Settings): string {
  return new URLSearchParams(
    Object.entries(settings).map(([key, value]) => [key, String(value)]),
  ).toString();
}

/** Render exactly 48 MSB-first bits, proportional field widths, and no inferred payload semantics. */
export function headerMarkup(raw: string): string {
  if (!/^[0-9a-fA-F]{12}/.test(raw))
    return '<p class="muted">No complete primary header is available for this record.</p>';
  const bits = [...raw.slice(0, 12)]
    .map((digit) => Number.parseInt(digit, 16).toString(2).padStart(4, "0"))
    .join("");
  const fields = [
    ["VER", 3],
    ["T", 1],
    ["S", 1],
    ["APID", 11],
    ["FLAGS", 2],
    ["SEQUENCE COUNT", 14],
    ["DATA LENGTH − 1", 16],
  ] as const;
  let position = 0;
  const sections = fields
    .map(([label, width], index) => {
      const start = position;
      position += width;
      return `<g class="field-${index % 3}"><rect x="${start * 20 + 1}" y="25" width="${width * 20 - 2}" height="30" rx="2"/><text x="${start * 20 + 5}" y="44">${label}</text></g>`;
    })
    .join("");
  const cells = [...bits]
    .map(
      (bit, index) =>
        `<g><rect class="bit-cell" x="${index * 20 + 1}" y="73" width="18" height="30"/><text class="bit-value" x="${index * 20 + 10}" y="93" text-anchor="middle">${bit}</text><text class="bit-index" x="${index * 20 + 10}" y="122" text-anchor="middle">${index}</text></g>`,
    )
    .join("");
  return `<svg viewBox="0 0 960 134" role="img" aria-labelledby="header-title"><title id="header-title">48-bit primary header, most significant bit first; field values also appear below</title>${sections}${cells}</svg>`;
}
