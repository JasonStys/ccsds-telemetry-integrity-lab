# CI and portable verification record

By Jason Stys. Observed 2026-10-20 local / 2026-10-21 UTC. Local evidence and test scope are in [VALIDATION](../VALIDATION.md).

## First published source

Source: `d03f1579a888e6440970362a6bcaf5bd922a325a`.

- [Validation 39522149313](https://github.com/JasonStys/ccsds-telemetry-integrity-lab/actions/runs/39522149313): **success**, all eight jobs. Linux Python 3.12/3.14, Windows/macOS Python 3.14, actual Linux three-engine browser suite and all three frozen application builds/smokes.
- Native tests: five passed, including exhaustive 65536-word and 65536-length checks plus 50000 hostile-byte records; Rust format/strict Clippy/release build passed in applicable configurations.
- Python: 188 passed per configuration; initial branch-inclusive coverage 97.68%. TypeScript: 11 unit tests. Browser: 24 acceptance checks. Deterministic contracts, documentation indexes, types/lint/format and advisory audits passed in their applicable jobs.
- [CodeQL 39522149239](https://github.com/JasonStys/ccsds-telemetry-integrity-lab/actions/runs/39522149239): workflow completed **successfully**, but produced one finding, `py/uninitialized-local-variable`, for the common return after fixture match dispatch. A successful job was therefore not treated as a clean review.

## Reviewed correction

The dispatch has been rewritten with explicit `if/elif/else`, retaining unknown-fixture rejection. The supported cases already assigned rows and the default raised; the change clarifies control flow rather than accepting new inputs or concealing a failing test. All 24 deterministic report hashes remain unchanged. Local rerun: all 188 tests passed, 97.67% Python coverage; two fewer executable statements account for the percentage change. No check, benchmark, branch case or CodeQL rule was removed/suppressed, and the finding was not manually dismissed.

This report cites completed prior evidence instead of claiming its own future commit has passed. Release preparation must use successful **Validation and CodeQL on the exact final source SHA**. Open alerts are inspected again before publication. Final release notes link those final runs plus the three-platform release workflow and downloaded ZIP checksums. A draft or one successful native build is not a complete release.

## Storage and reproducibility

After the first workflows, this repository had zero Actions artifact bytes and zero cache entries. No existing user runs/artifacts/caches were removed. Workflows do not upload Actions artifacts/caches; releases use a distinct asset category. Detailed owner account storage is not part of the public report.

All built-in captures are invented. No real mission data, credentials, private local history or machine-specific export paths appear in committed evidence. Timings are informational in job logs and excluded from evidence hashes. Rust compiler/standard-library notices are bundled with actual native applications; no external crate implementation is incorporated.
