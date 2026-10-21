# Licensing, toolchain and sources

By Jason Stys. Original code, invented captures and UI: [MIT](../LICENSE).

## Distribution

- Rust core: no external crates; `Cargo.lock` contains only this package. This does not mean the compiler/standard library has no third-party notices. Rust is MIT/Apache-2.0; texts are committed as `licenses/RUST-MIT.txt` and `RUST-APACHE.txt`.
- Native bundles include the exact compiler distribution's `COPYRIGHT-library.html` and associated license texts from its `share/doc/rust` tree, covering standard-library redistribution notices. The pinned `rust-docs` component is required for packaging, and missing notices fail the build. Toolchain docs are not served as application content.
- CPython/standard library notices are in [licenses/PYTHON.txt](../licenses/PYTHON.txt) and included in the bundle. Python application runtime uses only stdlib, plus the separately bundled original Rust executable.
- PyInstaller is distributed under its GPL license with bootloader exception. The locked distribution's `COPYING.txt`, including that exception, is included under bundle licenses; original app source remains MIT, not a claim that PyInstaller is MIT.
- Windows native worker statically links its MSVC CRT using the tracked target configuration. OS/runtime components retain their own licenses; no OS, browser or commercial driver is redistributed.
- Production browser output is original compiled TypeScript/HTML/CSS/SVG; no framework, chart library, remote fonts/artwork/AI assets or Node runtime is shipped.

## Development tools

Hash-locked Python graph: pytest/coverage/Hypothesis, Ruff, mypy, pip-audit, PyInstaller and transitives. Integrity-locked Node graph: TypeScript, Vite, Vitest, Playwright, axe and Prettier. Upstream distribution metadata/node_modules contains their license notices; dependencies are ignored, not committed. Compiler 1.98.1, format/Clippy components and Cargo lock are pinned; no Rust advisory scan is claimed for nonexistent third-party crates. GitHub's CodeQL licensing/service terms are distinct from project MIT; supported language coverage here is Python and JS/TS only.

Audits query current advisory services during development/CI, not app runtime. A no-known-vulnerabilities result is time-specific. Source locks are reproducibility inputs, not assurance that unknown flaws cannot exist.

## Research

Official [CCSDS Space Packet Protocol, 133.0-B-2 EC2 PDF](https://ccsds.org/Pubs/133x0b2e2.pdf) and [publication catalog](https://ccsds.org/publications/sls/), accessed 2026-10-20. Primary-header field layout and count/length interpretation inform the restricted parser. The document is linked, not redistributed; no external library implementation or mission dataset is copied. All golden vectors, corruptions and capture scenarios are original synthetic constructions, not official conformance vectors. Full protocol/PICS compliance is explicitly not claimed. No CCSDS, NASA, government, military or contractor endorsement/affiliation is implied.
