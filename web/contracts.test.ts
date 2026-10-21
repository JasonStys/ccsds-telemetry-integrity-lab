/** Pure finite controls, escaping and exact bit-graphic contracts by Jason Stys.
 * Variables: golden header, hostile preferences and markup strings. Lines: docs/CODE_INDEX.md.
 */
import { expect, it } from "vitest";
import { defaults, escapeText, headerMarkup, query, readPreferences } from "./contracts";

it("round-trips finite preferences and query", () => {
  expect(readPreferences(JSON.stringify(defaults))).toEqual(defaults);
  expect(new URLSearchParams(query(defaults)).size).toBe(3);
});
it.each([null, "null", "[]", "{}", "bad", "x".repeat(513)])(
  "rejects malformed preference input %s",
  (raw) => {
    expect(readPreferences(raw)).toBeNull();
  },
);
it("rejects prototype names, coercion, bool and extra keys", () => {
  for (const value of [
    { scenario: "toString" },
    { payload_limit: "128" },
    { forward_window: true },
    { unknown: 1 },
  ])
    expect(readPreferences(JSON.stringify({ ...defaults, ...value }))).toBeNull();
});
it("escapes dynamic text including quote delimiters", () => {
  expect(escapeText('<img a="x">&\'')).toBe("&lt;img a=&quot;x&quot;&gt;&amp;&#39;");
});
it("draws exactly 48 bits and a proportional field map from a golden header", () => {
  const html = headerMarkup("002ac0010002deadbe");
  expect(html.match(/class="bit-cell"/g)).toHaveLength(48);
  expect(html).toContain("SEQUENCE COUNT");
  expect(html).toContain('width="318"');
  expect(html).not.toContain("style=");
});
it("does not invent a header for truncated or nonhex input", () => {
  expect(headerMarkup("002ac0")).toContain("No complete primary header");
  expect(headerMarkup('<svg onload="x">')).not.toContain("<svg");
});
