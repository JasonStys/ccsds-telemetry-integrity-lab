# Input, native, HTTP and report contracts

By Jason Stys. Version 1.0.0; restricted offline synthetic telemetry profile.

## Lab capture format

ASCII only, one hex record per newline. Hex digits may be uppercase/lowercase, but no separators/spaces are accepted. CRLF normalizes; a final newline terminates the last record; an internal empty line is a zero-byte record. Empty input contains zero records. Limits: 131072 input bytes, 128 records, 8204 hex characters per record, supported payload caps 32/128/4096. A structurally valid larger standard packet can be outside this profile. See [MODEL](MODEL.md) for exact bit/length and error semantics.

```text
002ac0010002deadbe
002ac00200011122
```

The sample means two telemetry records, APID 42, counts 1 and 2, with three and two opaque data bytes respectively. No embedded time, CRC or units are implied. These hex values are invented, not captured traffic.

Envelope oversize/count/encoding failures reject the complete capture, before native evidence is emitted. Malformed individual records produce fixed error codes and remain alongside later independent records. Raw concatenated packets without a delimiter are not a supported stream format or recovery case. Imports are CLI-only; no HTTP upload/local-file/remote-fetch endpoint exists.

## Native worker

`telemetry-core <32|128|4096>` reads only stdin and writes one fixed-key JSON object per record, in the same order. No input path, shell, network, arbitrary executable or operational command interface exists. Exit 0 means the **capture envelope** was processed; rows may still be rejected. Exit 2 means a controlled envelope/argument/I/O failure, with a fixed stderr message. This is not an “all packets valid” exit-code contract.

Each native row has `code`, decoded `header` or null, `actual_size` or null (undecodable hex), and `payload_hex` (empty on rejection). Header fields: version, packet_type, secondary, apid, flags, sequence, data_length, expected_size. The worker never reflects raw imported text into its JSON; strings are generated hex or fixed labels. Error precedence follows [MODEL](MODEL.md).

The Python bridge runs only the checkout's fixed Cargo release path or bundled native resource. It checks the finite cap, input envelope, five-second timeout, process success, bounded output and row/cardinality contract. It compares **every native result** against the independent reference; disagreement causes a controlled failure, not a partial or substituted report. An unavailable worker never triggers a Python success fallback.

## Read-only HTTP

Only `127.0.0.1:<port>` is bound. Host must exactly match; Origin must be absent or the exact same origin; cross-site Fetch Metadata is denied. No CORS. All responses set restrictive CSP, no-store, MIME/frame/referrer/sensor policies. The target is bounded to 1024 characters, at most eight query fields, no duplicates/unknowns. GET only; mutation methods/HEAD are rejected.

| Route                       | Parameters / result                                                                     |
| --------------------------- | --------------------------------------------------------------------------------------- |
| `/api/health`               | No query; fixed local educational health                                                |
| `/api/catalog`              | No query; finite scenarios, choices and defaults                                        |
| `/api/run`                  | Optional scenario/payload_limit/forward_window; full evidence JSON; no format parameter |
| `/api/report`               | Same settings plus `format=json\|csv\|html\|input`; fixed attachment name               |
| `/`, `/assets/<built-name>` | Exact confined built assets; no filesystem browsing or query                            |

Defaults: nominal, payload_limit 128, forward_window 256. Finite forward values 16/256/8191. Unsupported parameters give 400; bad Host/origin/site 403; disallowed/missing files 404; methods 405; oversized target 414; missing native/local resources 500. Failures use generic messages without local paths/stack traces. Threaded localhost HTTP is **not a public production server**, authentication system or global request quota.

## Evidence

- `id`: SHA-256 of canonical compact sorted UTF-8 JSON, excluding id itself. A content identifier, not a signature.
- `version`, `scenario` (or local-hex), effective `settings`, normalized capture, note and provenance.
- `rows`: native fields plus original record text, index, normalized text hash, continuity disposition, receipt-time unobserved_values, baseline_advanced and review flag.
- `totals`: record/accepted/rejected/review/idle counts and sum of receipt-time gap-value observations. Accepted includes idle/review. Gap sums are not reconciled unique packet-loss counts and are not revised when delayed records arrive.

Full JSON is authoritative. CSV is one row per record, excluding raw imported text/payload so formulas/markup cannot enter cells; it is not a lossless full-report substitute. HTML is complete escaped JSON, no scripts/styles/active content, with an inert CSP. Input capture exports normalized complete record text for reimport. Filenames are fixed: `telemetry-evidence.json`, `telemetry-records.csv`, `telemetry-evidence.html`, `telemetry-capture.hex`. Filters and selected-record detail never alter full exports. Imported provenance changes the report hash even if the underlying native results match a fixture.

## Local history

`--history PATH` explicitly opts into a local SQLite database. The run SHA is checked, values are parameterized, insertion is immediate/transactional, identical IDs are idempotent, collisions fail, update/delete triggers protect rows and a 100-report cap refuses additional entries without deleting anything. Choose a new explicit path when full. The database is unencrypted local data, not protected from an OS administrator or database editor; use OS controls and keep it out of Git. History/export are separate destinations with no cross-file atomicity guarantee.
