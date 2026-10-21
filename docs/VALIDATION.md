# Validation strategy and observed local results

By Jason Stys. Observed 2026-10-20 on Windows x64, Rust 1.98.1, CPython 3.14.6 and Node 24.18.1. After the explicit-dispatch review change, all 188 Python tests still pass with **97.67%** branch-inclusive coverage (two fewer executable statements; no test or gate removed). The initial measured coverage in the table below was 97.68%. Remote CI evidence is recorded only after actual runs; see [reports/ci-baseline.md](reports/ci-baseline.md).

| Gate                                       | Observed result                                                                                                                                            |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Rust native unit suite                     | Five tests passed, including every 65536 identification word and every 65536 encoded length                                                                |
| Seeded hostile-byte campaign               | 50000 records inside the native suite; bounded sizes, round-trip hex and accepted-packet invariants                                                        |
| Rust lint/format/build                     | Pinned compiler, forbidden unsafe, strict Clippy `-D warnings`, rustfmt and release build passed                                                           |
| Python/native tests                        | 188 passed; 97.68% branch-inclusive Python coverage (minimum 90%)                                                                                          |
| Finite fixture grid                        | All 108 configurations repeat deterministically and agree cross-language; included above                                                                   |
| Property-based cross-language checks       | 100 arbitrary-record-list examples plus 100 independently constructed valid-body/segmentation examples; actual Rust worker compared with arithmetic Python |
| TypeScript unit suite                      | 11 passed; preferences, prototype/coercion rejection, escaping, exact 48-bit graphic and missing-header behavior                                           |
| Three-engine browser suite                 | 24 passed, eight each in Chromium, Firefox and WebKit against actual Rust/service/build                                                                    |
| Deterministic report contracts             | 24 fixture/cap evidence hashes and summaries passed                                                                                                        |
| Ruff / strict mypy / production TypeScript | Passed locally                                                                                                                                             |

The actual local Windows frozen application passed JSON export, production HTML/assets, health and sequence-gap API smoke with its bundled Rust executable. Both dependency audits reported no known vulnerabilities at check time (npm: zero reported; pip-audit: no known vulnerabilities). These are observed local outcomes, not guarantees against unknown flaws.

Uncached full worker+analysis timing during development was approximately 14.4 ms median over 20 small unsupported-profile runs on this PC. It includes IPC/startup/reference work, not just native parsing. Timings are descriptive—not a hard-real-time, throughput, memory-benchmark or flight-platform claim—and excluded from canonical evidence. CI prints its own measurements without a flaky machine-specific threshold. [reports/benchmark.json](reports/benchmark.json) is reviewed deterministic output, not invented historical results.

## Layered tests and traceability

| Requirement                        | Evidence                                                                                                                                                                                                 |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Safe bounded primary-header decode | Native exhaustive identification/length loops, min/max/zero-data cases, Rust borrow test, forbidden unsafe and hostile-byte invariants                                                                   |
| Independent correctness            | Manual golden vector; Python fields use division/remainder vs Rust masks; every production row compared; explicit disagreement test withholds evidence                                                   |
| No swallowed next record           | Truncated/false-length/nonhex records followed by accepted records; raw concatenation rejected; no guessed resync assertion                                                                              |
| Precise continuity semantics       | Wrap, interleaved APIDs, idle isolation, repeat/reuse, late/reset, narrow-window forward review and half-range ambiguity tests                                                                           |
| Honest content limits              | Mutated payload still accepted; note and browser regression forbid false payload-integrity assurance                                                                                                     |
| Envelope/worker failure handling   | Native CLI argument/count/size/encoding failures; bridge missing/malformed/oversized/cardinality cases; no fallback                                                                                      |
| Input/export integrity             | CLI overwrite refusal/import limits, full JSON, safe CSV exclusion, escaped HTML, normalized input, deterministic SHA                                                                                    |
| Local SQL integrity                | Hash checking, idempotence, parameter binding, immutable update trigger and full-history refusal without pruning                                                                                         |
| HTTP protections                   | Actual loopback sockets for Host/origin/site, exact paths/symlink confinement, duplicate/unknown/excessive query, methods, fixed downloads, generic errors and target size                               |
| UI behavior/accessibility          | Ledger/header inspection, filter vs full totals, profile changes, 0-record case, four real downloads, error/retry, hostile-response escaping, opt-in preferences, 390px layout, axe and keyboard regions |
| Portable app resources             | Actual frozen executable CLI export plus web assets/health/scenario API, including native Rust and bundled notices; results recorded after execution                                                     |

Rust's five named tests contain many cases; they are not 181072 independently named unit tests. Python coverage applies only to the Python modules, not Rust machine code. Rust coverage percentage, formal proof, coverage-guided libFuzzer, Miri, sanitizers, penetration testing and operational telemetry validation are **not claimed**. Seeded mutation/generation checks are reproducible campaigns, not guarantees all possible input bugs were found.

## Development findings

The compiler rejected a short-lived borrowed array in an exhaustive **test fixture**; assigning the array a scoped owner fixed its lifetime without changing production bounds. Strict Clippy requested fixed-size `as_chunks` use; the hex decoder was updated rather than suppressing the lint. A copied HTTP test was corrected to exercise an actual duplicate payload_limit field instead of merely an unknown field. Browser keyboard-scroll and hostile-response checks were present from the initial UI implementation; no axe rule was disabled. These are software verification results, not evidence of full CCSDS conformance or payload authenticity.

The first CodeQL workflow completed successfully but reported `py/uninitialized-local-variable` at the common return after fixture `match` dispatch. Every case assigned rows and the default raised; finite-case and unknown-case tests passed. The dispatch was rewritten as explicit `if/elif/else` with the same strict unknown-case failure so assignment flow is clear to readers and the analyzer. All 24 reviewed hashes remain byte-identical, and all 188 tests still pass. The finding is not manually dismissed or suppressed; final publication requires inspecting the fresh scan result. Debug/code-review guidance informed the reproduce/isolate/refactor/regression process.

The design/testing skills shaped the independent reference gate, bounded trust boundaries and accessible textual equivalents; release guidance requires actual exact-source CI and executable smoke, not a badge-only handoff.

## Storage and verification limits

Actions storage was checked before implementation using live artifact inventory and the current billing meter, with the account-level details reported privately to the owner. Billing accumulation, current artifacts and separate caches are distinct measures. Existing runs/artifacts/caches were left untouched. This repository's workflows upload no Actions artifacts/caches; release assets are separate.

CI adds four OS/Python test configurations, three native builds and three Linux browser engines. Native platform success does not prove every OS distribution, device, endpoint policy or assistive technology. Advisory scans are current-service observations, not absence-of-all-vulnerabilities proofs. No real radio/link, mission telemetry, payload meaning/units, secondary header, segmentation/reassembly, raw sync, CRC/authentication, sender identity, unique/permanent loss reconciliation, signed binary or flight qualification was validated.
