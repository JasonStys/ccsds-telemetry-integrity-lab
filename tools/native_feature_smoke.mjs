/** Jason Stys — actual extracted APID timeline recovery, original decisions and evidence download.
 * Functions: owned journey; variables: independently expected50,52,51,53 counters and provisional gap.
 * Exact lines: docs/CODE_INDEX.md. No packet authentication, live stream or operational decoder claim.
 */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect } from "@playwright/test";
import { runNativeJourney } from "./native_browser.mjs";

await runNativeJourney(async ({ page, request, outputDirectory, version }) => {
  await expect(page.getByRole("status")).toContainText("Inspection complete");
  await page
    .getByRole("combobox", { name: "Capture scenario", exact: true })
    .selectOption("out-of-order");
  await page.getByRole("button", { name: "Inspect capture" }).click();
  await page.locator("#apid-timelines summary").first().click();
  await expect(page.locator("#apid-timelines")).toContainText("provisional-gap-recovery");
  const run = await (await request.get("api/run?scenario=out-of-order")).json();
  assert.equal(run.version, version);
  const timeline = run.apid_timelines[0];
  assert.equal(timeline.apid, 42);
  assert.deepEqual(
    timeline.events.map((event) => event.sequence),
    [50, 52, 51, 53],
  );
  assert.deepEqual(
    [timeline.provisional_total, timeline.recovered, timeline.outstanding],
    [1, 1, 0],
  );
  assert.equal(timeline.gaps[0].status, "recovered");
  assert.deepEqual(timeline.gaps[0].recoveries, [{ sequence: 51, record: 2 }]);
  assert.equal(timeline.events[2].original_decision, "late-or-reset");
  assert.equal(run.rows[2].disposition, "late-or-reset");
  // Recovery explains later evidence; the original parser/review totals are never rewritten.
  assert.equal(run.totals.review, 2);
  await page
    .locator("#apid-timelines li")
    .filter({ hasText: "provisional-gap-recovery" })
    .getByRole("button")
    .click();
  await expect(page.locator("#inspection")).toContainText("late or reset");
  const pending = page.waitForEvent("download");
  await page.getByRole("link", { name: "Full JSON ↓", exact: true }).click();
  const download = await pending;
  const file = path.join(outputDirectory, "native-apid-recovery.json");
  await download.saveAs(file);
  assert.deepEqual(JSON.parse(await readFile(file, "utf8")), run);
  await page
    .getByRole("combobox", { name: "Capture scenario", exact: true })
    .selectOption("empty-capture");
  await page.getByRole("button", { name: "Inspect capture" }).click();
  await expect(page.locator("#apid-timelines")).toHaveText("No accepted non-idle APID streams.");
  assert.equal((await request.get("api/run?payload_limit=0")).status(), 400);
});
