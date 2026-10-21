# Release verification and rollback

By Jason Stys. Manual workflow creates drafts only; no auto-publishing binary pipeline.

## Before release

Review the supported packet profile, continuity ambiguity, content-integrity blind spot, synthetic provenance, threat model and notices. Run Rust tests/format/Clippy, Python coverage/lint/types, deterministic contracts/indexes, Node unit/build/format/audit and all browser engines. Native core must build before Python tests. Packaging requires the pinned toolchain's rust-docs notices, production UI, PyInstaller lock and built Rust executable; `python tools/package_app.py` verifies these and runs the actual frozen CLI/service/native API before ZIP creation.

Check Actions artifact inventory and current billing meter before workflows; never repeat old cleanup consent. Existing user evidence/caches are not deleted. No Actions artifact/cache uploads exist in these workflows; direct release assets are a separate category.

Push reviewed source and require Validation and CodeQL success on the exact commit. CodeQL analyzes Python/TypeScript only; Rust has compiler/forbidden-unsafe/Clippy/native-property verification, not a false CodeQL support claim. Inspect open code-scanning findings in addition to green workflow conclusions.

## Build and publish

Dispatch `Portable release` on main with a new digits.digits.digits version. Preparation validates the version, checks successful exact-source Validation/CodeQL and creates a draft targeted to that SHA. Three OS jobs build the pinned Rust native executable, website and frozen service; smoke the actual executable; create ZIP plus SHA-256; then upload the single platform pair directly to the draft. Existing tags/assets are never overwritten by the helper.

All three jobs must pass and six assets be present before publishing. Download/verify every ZIP/checksum pair. Extract the Windows release into a new local directory; run its actual frozen export/server smoke plus input/history round-trip if this PC supports it. Linux/macOS execution is native CI evidence, not a claim it ran on this Windows PC. Review source/tag SHA, check links, checksum table, architecture, unsigned limitations and scope in release notes, then publish the draft. Failed preparation or one failed platform is not a successful release.

Filenames report actual native OS/architecture, expected Linux x86_64, Windows AMD64 and macOS ARM64. These are unsigned/not notarized portable applications, not universal/Linux-distribution/mobile installers. Never bypass OS protection. Byte-identical reproducible executables, formal conformance and zero unknown vulnerabilities are not promised.

## Rollback

There is no auto-updater/system service/global install/migration. Stop the process, preserve local exports/history privately and use a previous verified release/tag in a separate directory. Do not rewrite published tags/assets, overwrite a running bundle, delete history or rebaseline hashes to conceal a regression. Changes to profile/framing/state/limits need fresh design and independent tests; dependency upgrades require reviewed locks, complete gates and a new version. Keep generated line indexes current after formatting. Report minimized synthetic issues without sensitive data.
