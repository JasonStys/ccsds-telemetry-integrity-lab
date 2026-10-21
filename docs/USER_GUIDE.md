# User guide and troubleshooting

By Jason Stys. Use only synthetic, non-sensitive local captures. No account or live connection required.

## Portable application

Download the ZIP for your exact OS/architecture and its `.sha256` from Releases. Compare the **full** digest before extraction. Windows: `Get-FileHash -Algorithm SHA256 <zip>`. Linux: `sha256sum -c <checksum-file>`. macOS: `shasum -a 256 <zip>` and compare with the manifest. Extract the entire directory, keeping `_internal`, native worker and notices with the launcher. Launch `TelemetryIntegrityLab.exe` on Windows or `TelemetryIntegrityLab` on the supplied Linux/macOS architecture. A verified Unix file may need its executable bit restored with `chmod +x TelemetryIntegrityLab` in the extracted folder.

The console prints an ephemeral `http://127.0.0.1:<port>/` address and opens your browser. Keep it running; Ctrl-C stops the application. If browser auto-open fails, copy that exact printed local address. No global Rust/Python/Node or administrator access is needed by the bundled application.

Bundles are unsigned/not notarized. Do not disable antivirus, bypass SmartScreen/Gatekeeper/browser warnings, remove quarantine, run elevated or change firewall policy. Source-run after review if your policy does not permit unsigned software. There is no installer, system service, auto-updater or mobile binary. The browser layout is responsive, but remote phone access is deliberately not enabled; never tunnel/proxy the local service publicly.

## Inspect the evidence

1. Select a scenario, payload cap and forward review window. Changing controls hides old evidence until another inspection, preventing stale exports.
2. Inspect capture. Complete totals include every record: accepted includes idle and continuity-review records. Rejected is structural/profile failure, not proof of maliciousness.
3. Filter the ledger if useful. Filters affect only displayed rows; totals, downloads and selected-record detail remain labeled complete evidence. Capture order is not elapsed time.
4. Use a record's Inspect button to show native outcome, 48-bit primary header, decoded fields, actual/declared size and opaque bytes. An incomplete header is not guessed. On mobile, tab to the labeled scrollable ledger/header region and use arrow keys to scroll.
5. Compare wraparound, delayed-after-gap, repeat/reuse and half-range ambiguity cases. A gap event is not permanent unique loss; delayed records may arrive afterward, and counter cycles/resets cannot be uniquely reconstructed.
6. Try the payload-bit-flip case. All headers still pass. The system explicitly cannot establish payload correctness/authenticity from these checks.
7. Download full JSON for complete evidence, record CSV for a compact non-lossless table, inert HTML for portable reading, or normalized hex capture for reimport.

No records supplied is a legitimate empty capture. It is not proof that a packet was validated. No native worker/reference agreement means no evidence: the UI offers manual retry, not a simulated success.

## Explicit local captures and history

From source, use `python -m packetlab`. From a bundle use `TelemetryIntegrityLab export ...` (`.\TelemetryIntegrityLab.exe` in a Windows PowerShell current folder). Same arguments:

```text
python -m packetlab export --scenario nominal --format input --output my-capture.hex
python -m packetlab export --input my-capture.hex --payload_limit 128 --forward_window 256 --output review.json --history local-history.sqlite3
```

[API](API.md) specifies ASCII/newline boundaries, caps and strict field semantics. There is no file upload in the browser and no automatic directory scan. Existing output files are never overwritten. History is explicit local unencrypted SQLite with immutable rows and a 100-run cap; choose a new database path when full. Do not commit private history/exports. History/export are separate operations, so a history insert can succeed even if later file creation fails. Use normal OS permissions/full-disk encryption and backups where needed.

## Preferences and common failures

Remember controls is off by default; opting in stores only the three finite controls at this browser origin. Uncheck to remove them. Packets/evidence/accounts are never stored there. Blocked browser storage is nonfatal. An ephemeral relaunch can use a different origin/port and therefore not see earlier settings.

- Native worker missing: source users run `cargo build --release --locked`; bundle users re-extract the whole verified ZIP. Python is not a fallback decoder.
- Missing website assets: run `npm ci` and `npm run build`, or re-extract the whole bundle.
- Port conflict: omit `--port` to use an ephemeral port.
- API failure: check the local console and retry manually; stale evidence remains hidden.
- Whole capture rejected: check ASCII encoding, 128 KiB cap and 128-record limit. Do not remove limits just to accept arbitrary files.
- Individual record rejected: inspect exact code/size. A valid but unsupported standard variant is not necessarily corrupt.
- Resource mismatch/reference disagreement: stop trusting the result and report a minimized synthetic reproduction. Do not disable the comparison gate.

Full model and evidence: [MODEL](MODEL.md), [VALIDATION](VALIDATION.md). Contact/bugs: [Jason Stys](https://github.com/JasonStys), [repository issues](https://github.com/JasonStys/ccsds-telemetry-integrity-lab/issues). Never post tokens, private captures, sensitive paths or operational mission data.
