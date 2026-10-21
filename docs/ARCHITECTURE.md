# Architecture and decisions

By Jason Stys. Implemented scope: one bounded local packet-inspection lab.

```text
Browser finite scenario/profile → loopback read-only HTTP ─┐
CLI explicit ASCII capture → envelope validation ──────────┤
                                                          ↓
                         trusted fixed Rust stdin worker + independent Python reference
                                                          ↓ exact agreement required
                         per-APID continuity review → canonical complete evidence
                                                          ↓
                         UI / JSON / CSV / inert HTML / input capture
CLI explicit --history → verified immutable local SQLite (100-run cap)
```

## ADR 001 — Rust for untrusted bytes, Python for independent inspection

Rust is suited to explicit byte bounds, borrowing and forbidden unsafe code without an external runtime dependency. The production `inspect` function borrows accepted payload bytes and never overlays a packed C structure. A zero-crate worker emits fixed-key JSON without reflecting imported text; output strings are constants or generated hex. Only its own package/build artifact path can be launched, with no shell or caller executable option.

Python independently extracts fields through integer division/remainder and conventional bytes, not a shared binding that would merely restate the same implementation. Every actual worker output must match; otherwise the application fails closed and shows no report. This costs process startup and duplicate work but makes the portfolio's verification claim inspectable. It is not a “production fastest decoder” claim or formal proof that independent implementations cannot share a mistaken specification interpretation.

## ADR 002 — Honest, supplied record boundaries

Packet headers alone are not used as trustworthy sync markers. A separate original newline-hex lab container supplies boundaries. Full-envelope failures produce no partial native stdout; per-record failures remain evidence, and later records can be analyzed independently. This explicitly trades real stream/transfer-frame support for a bounded, testable parsing problem. Future raw-frame integration is a new design with authoritative framing/error-control requirements, not an arbitrary recovery checkbox.

## ADR 003 — Separate structure, policy, and payload integrity

Native Rust validates only the supported primary-header/data profile. Python adds original per-APID receipt policy without changing packet bytes. UI separately labels rejection, structural acceptance, idle and continuity review. No unsupported packet is automatically treated as malicious; no gap becomes definite permanent loss; no accepted header establishes authentic content. The bit-flip case intentionally demonstrates that blind spot.

## ADR 004 — Local-only browser application

TypeScript/HTML/CSS/SVG provide typed controls, escaped rendering, readable ledger and 48-bit inspection without CDN/font/chart/AI services. The stdlib Python handler binds IPv4 loopback only, constrains Host/origin/site/path/query, sets strict CSP and exposes no upload, arbitrary file, command, history or remote-fetch endpoint. This is not an Internet-hardened multi-tenant service and must not be tunneled/proxied publicly. CLI imports/persistence are explicit local operations.

The browser cancels obsolete requests and hides stale results after control changes/failures. Preferences are off by default, finite-validated and contain controls only. A filter changes the ledger, not full totals/downloads. Bit graphics have equivalent textual field values, and scrollable tables/bit strips are labeled keyboard-focusable regions.

## ADR 005 — Evidence and distribution

Canonical JSON IDs identify complete inputs, effective controls, provenance and outputs without machine-dependent paths/timings. SQL uses verified content IDs, parameters, immutable triggers and bounded explicit storage; exported files never overwrite. There is no cross-file transaction between export and history and no encryption-at-rest claim.

PyInstaller packages the Python stdlib service, native Rust executable and production browser assets. Static MSVC CRT linkage reduces Windows redistributable dependency; Rust/CPython/PyInstaller and standard-library redistribution notices are included. Native smoke executes the actual frozen CLI/service/Rust resources before ZIP creation. Bundles are unsigned, architecture-specific and have no privileged installer, auto-updater or phone-native component.

## ADR 006 — Storage-conscious CI and exact-source releases

Validation covers four OS/Python configurations, Rust format/Clippy/native tests, Python lint/types/coverage, deterministic contracts, browser unit/acceptance, advisory audits and three frozen apps. CodeQL covers only supported Python/JS/TS languages. Actions are SHA-pinned; Rust/compiler and dependency locks are explicit. There are no external Rust crates to claim were audited. Workflows upload no Actions artifacts/caches; release ZIP/checksum pairs are uploaded directly to a draft, which is a separate storage category.

Release preparation requires passing Validation and CodeQL on the exact source commit. All three native jobs must succeed, downloads/digests must be reviewed, then the draft can be published. Failed checks are investigated rather than disabled. Future scale, concurrency quotas, actual ground-system integration, authentication or cryptographic packet assurances require a new threat model and independent review.
