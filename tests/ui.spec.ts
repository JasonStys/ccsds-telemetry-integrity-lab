/** Real Rust/service/browser acceptance tests by Jason Stys.
 * Functions: ready, inspectCase and eight end-user contracts. Variables: download paths,
 * ledger/detail/filter states, keyboard/mobile and hostile-response checks. Lines: docs/CODE_INDEX.md.
 */
import { readFile } from "node:fs/promises";
import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/** Wait for actual parser/reference evidence, not merely static HTML. */
async function ready(page: Page): Promise<void> {
  await page.goto("/");
  await expect(page.getByRole("status")).toContainText("Inspection complete");
}
/** Submit a finite scenario and wait for refreshed parser evidence. */
async function inspectCase(page: Page, scenario: string): Promise<void> {
  await page
    .getByRole("combobox", { name: "Capture scenario", exact: true })
    .selectOption(scenario);
  await page.getByRole("button", { name: "Inspect capture" }).click();
  await expect(page.getByRole("status")).toContainText("Inspection complete");
}

test("native/reference gap evidence and exact header bits are inspectable", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await ready(page);
  await inspectCase(page, "sequence-gap");
  await expect(page.locator("#agreement")).toHaveText("4 / 4 parser agreement");
  await page.getByRole("button", { name: "Inspect record 3", exact: true }).click();
  await expect(page.locator("#inspection")).toContainText("3 sequence values were not observed");
  await expect(page.getByRole("img", { name: "48-bit primary header" })).toBeVisible();
  await expect(page.locator(".bit-cell")).toHaveCount(48);
  expect(errors).toEqual([]);
});
test("wraparound, delayed records and duplicates retain separate meanings", async ({ page }) => {
  await ready(page);
  await inspectCase(page, "wraparound");
  await expect(page.getByRole("status")).toContainText("0 for continuity review");
  await inspectCase(page, "out-of-order");
  await expect(page.locator("#records")).toContainText("late or reset");
  await inspectCase(page, "duplicate-and-reuse");
  await expect(page.locator("#records")).toContainText("repeat of baseline");
  await expect(page.locator("#records")).toContainText("counter reuse");
});
test("rejected records recover at trusted boundaries and filter does not change totals", async ({
  page,
}) => {
  await ready(page);
  await inspectCase(page, "truncated-and-length");
  await expect(page.locator("#records tr")).toHaveCount(5);
  await page.getByRole("combobox", { name: "Show records", exact: true }).selectOption("rejected");
  await expect(page.locator("#records tr")).toHaveCount(3);
  await expect(page.locator("#agreement")).toHaveText("5 / 5 parser agreement");
  await page.getByRole("button", { name: "Inspect record 4", exact: true }).click();
  await expect(page.locator("#inspection")).toContainText("=FORMULA");
  await expect(page.locator("#scenario-note")).toContainText(
    "Raw CCSDS byte-stream resynchronization is not implemented",
  );
});
test("profile caps, corruption limitation and empty input are truthful", async ({ page }) => {
  await ready(page);
  await inspectCase(page, "payload-limit");
  await expect(page.locator("#records")).toContainText("profile payload limit");
  await page.getByRole("combobox", { name: "Payload limit", exact: true }).selectOption("4096");
  await expect(page.locator("#results")).toBeHidden();
  await page.getByRole("button", { name: "Inspect capture" }).click();
  await expect(page.getByRole("status")).toContainText("0 rejected");
  await inspectCase(page, "payload-corruption");
  await expect(page.locator("#scenario-note")).toContainText("no payload checksum");
  await expect(page.getByRole("status")).toContainText("0 for continuity review");
  await inspectCase(page, "empty-capture");
  await expect(page.locator("#agreement")).toHaveText("0 / 0 parser agreement");
  await expect(page.locator("#inspection")).toContainText("No records supplied");
});
test("all four actual downloads preserve complete evidence and safe CSV", async ({ page }) => {
  await ready(page);
  await inspectCase(page, "truncated-and-length");
  for (const [label, name, snippet] of [
    ["Full JSON ↓", "telemetry-evidence.json", '"records": 5'],
    ["Record CSV ↓", "telemetry-records.csv", "truncated-header"],
    ["HTML report ↓", "telemetry-evidence.html", "Telemetry integrity evidence"],
    ["Input capture ↓", "telemetry-capture.hex", "=FORMULA"],
  ] as const) {
    const waiting = page.waitForEvent("download");
    await page.getByRole("link", { name: label, exact: true }).click();
    const download = await waiting;
    expect(download.suggestedFilename()).toBe(name);
    const path = await download.path();
    const text = await readFile(path!, "utf8");
    expect(text).toContain(snippet);
    if (name.endsWith(".csv")) expect(text).not.toContain("=FORMULA");
  }
});
test("service failure withholds stale results and explicit retry recovers", async ({ page }) => {
  await page.route("**/api/run?**", (route) => route.fulfill({ status: 503, body: "unavailable" }));
  await page.goto("/");
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.locator("#results")).toBeHidden();
  await page.unroute("**/api/run?**");
  await page.getByRole("button", { name: "Retry inspection" }).click();
  await expect(page.getByRole("status")).toContainText("Inspection complete");
});
test("unexpected markup remains inert in all rendered data fields", async ({ page }) => {
  const payload = '<img src=x onerror="alert(1)">';
  await page.route("**/api/run?**", async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    body.totals.accepted = payload;
    body.rows[0].raw_hex = payload;
    body.rows[0].header.apid = payload;
    await route.fulfill({ response, json: body });
  });
  await ready(page);
  await expect(page.locator("#metrics")).toContainText(payload);
  await expect(page.locator("#inspection")).toContainText(payload);
  await expect(page.locator("#results img")).toHaveCount(0);
});
test("opt-in preferences, mobile keyboard access, axe and restrictive headers", async ({
  page,
  request,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await ready(page);
  expect(await page.evaluate(() => localStorage.length)).toBe(0);
  await page.getByRole("checkbox", { name: "Remember controls" }).check();
  await inspectCase(page, "sequence-gap");
  await page.reload();
  await expect(page.getByRole("status")).toContainText("Inspection complete");
  await expect(page.getByRole("combobox", { name: "Capture scenario", exact: true })).toHaveValue(
    "sequence-gap",
  );
  await page.getByRole("checkbox", { name: "Remember controls" }).uncheck();
  expect(await page.evaluate(() => localStorage.length)).toBe(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(scan.violations).toEqual([]);
  await page.getByRole("region", { name: "Scrollable primary header" }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("region", { name: "Scrollable primary header" })).toBeFocused();
  await page.getByRole("combobox", { name: "Capture scenario", exact: true }).focus();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("combobox", { name: "Payload limit", exact: true })).toBeFocused();
  expect((await request.get("/api/health")).headers()["content-security-policy"]).toContain(
    "frame-ancestors 'none'",
  );
});
