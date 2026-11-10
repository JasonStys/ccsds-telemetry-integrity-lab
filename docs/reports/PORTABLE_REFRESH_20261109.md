# Portable release refresh validation — 2026-11-09

By Jason Stys. Version 1.1.0 prepares per-APID provisional gap recovery timelines that preserve original parser decisions and explicit ambiguity boundaries.

## Recorded checks

Windows/Python3.14.6:262 Python tests passed with98.08% combined coverage (unchanged90% gate),11 TypeScript tests and27 real source Chromium/Firefox/WebKit journeys passed. Rust1.98.1 formatting/Clippy/build and all5 native tests passed, including the existing50000-record seeded fuzz test. Strict mypy/Ruff/build passed. All24 original cross-language numerical totals remain unchanged; independent restoration of the previous product-version field reproduces every old evidence hash before version-only golden IDs are refreshed. The actual extracted API/UI verifies50,52,51,53 counters, one recovered provisional gap, unchanged late-or-reset decision/review totals, empty stream and exactJSON export; required native runtime notices also pass.

The actual Windows archive was inspected and extracted into a fresh temporary directory. Its executable ran from an unrelated working directory, preserved every previous native smoke contract, served only its owned loopback URL, matched package/version/instance identity, delivered actual compiled assets and completed the new real Chromium workflow/export. Local archive SHA-256: `595b0c3b455002e7632686c676d356d95f35d48422f470e348fb68dc9d774d47`. This development archive honestly records dirty-source metadata; it is local acceptance evidence rather than a published clean-source release.

Seventy new release/archive/runtime tests use independent GitHub metadata fixtures and actual small archive bytes. They reject wrong source/version/repository, running/failed/incomplete/ambiguous workflow histories, existing draft/tag/public release, asset/checksum/metadata mismatch, link/path escape and corrupt frozen identity. Release guards remain active under optimized Python. No GitHub writes occur in these tests. Existing coverage, native/oracle, security and browser gates remain unchanged.

## Reproduce and limits

Use exact development locks and target native toolchains. Run the repository's full coverage suite, deterministic benchmark, strict lint/types/index/format checks, TypeScript tests/build and three-engine source browser suite, then `python tools/package_app.py`. The last command launches the real extracted application and its new feature in Chromium; it needs Node/Playwright only as build-time acceptance tools. Ordinary users need neither Python nor Node.

Restricted record-delimited CCSDS telemetry profile only; no live radio/spacecraft connection, raw byte-stream resynchronization or payload authentication. Late arrival reconciliation explains provisional gaps without proving physical sender sessions or permanent packet loss.

Local native acceptance covers Windows only. Linux/macOS executable, links, ABI and UI still require real native CI. These unsigned portable folders are not installers or clean-machine installation proof. Native tests bypass the default OS browser opener, whose frozen POSIX inherited-library behavior remains a manual desktop check. No accounts, previous releases or user histories are changed. No push, dispatch, tag or release mutation was performed by this local work. The coordinator must review clean exact-source main checks, all three native jobs and all six uploaded assets/checksum digests before publishing.
