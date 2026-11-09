# APID review validation — 2026-11-09

- 192 Python tests passed on Windows / Python 3.14.6. Overall statement/branch coverage: 97.96%; new timeline module: 100%.
- Five real Rust kernel tests passed, including exhaustive identification/length boundaries and 50,000 seeded hostile byte records. The native parser is unchanged. Cargo locked release build, fmt and clippy with warnings denied passed.
- Eleven TypeScript unit tests and the strict production build passed. All 27 production-service browser tests passed across Chromium, Firefox and WebKit, including real late-recovery inspection, ambiguity and empty-stream review, downloads, mobile accessibility, inert rendering and restrictive headers.
- Ruff lint/format, mypy, dependency audits (no known Python vulnerabilities / zero npm vulnerabilities) passed. Original parser/decision totals in all 24 golden fixtures were independently compared unchanged before updating hashes for the added ledger. Golden contracts and exact-line documentation are verified.

Independent hand-computed cases exercise modulo wrap, late recovery, repeated recovery, counter reuse, half-range and unmatched-reset boundaries, cross-APID/idle/rejected isolation and the widest compressed gap. The first new browser assertion selected a later in-order packet instead of the recovery packet; it was corrected to select the named recovery event, then all three engines passed. No production guard was relaxed.

Tests use safe local fixture files and isolated loopback services, with scoped socket permission where the Windows sandbox blocks local connections. There were no child-triggered Actions runs, pushes or merges. Remote integration, cross-platform portable builds and source review remain the parent's responsibility. This is a restricted educational protocol viewer, not operational ground software; counter recovery does not prove content integrity or actual sender sessions.
