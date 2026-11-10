# CCSDS Telemetry Integrity Lab handbook

By Jason Stys.

The released 1.1.0 portable integrity lab includes per-APID continuity timelines: inspect provisional gaps and late recovery, follow ambiguity boundaries and retain every original parser decision in the downloaded evidence.

The safe Rust parser, independent Python reference and seeded fuzz checks remain unchanged. An extracted-app journey independently checks counters 50, 52, 51 and 53, a recovered provisional gap and unchanged late-or-reset review totals, then compares the real downloaded report with the API result. Coherent Cargo/Python/npm versions and runtime notices keep the new portable release aligned with its source.

## Read the documentation

| Edition                                                      | Audience and contents                                                                                              |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| [project-guide.docx](reports/project-guide.docx)             | User and developer guide: purpose, current usage, design, boundaries and source references.                        |
| [validation-review.docx](reports/validation-review.docx)     | Reviewer edition: exact tested baseline, observed workflows, dated local results and remaining limits.             |
| [validation-evidence.xlsx](reports/validation-evidence.xlsx) | Two filterable Excel Tables for observed workflows and test-source inventory, with recalculating outcome formulas. |

The editable Markdown remains the maintenance source. The Word files are readable editions, and the workbook is an evidence index rather than a test runner. See [publication identities and review](reports/publications.json) and the [documentation refresh record](reports/documentation-refresh-2026-11-09.md).

## Current usage and help

[README quick start](../README.md) is the entry point. Use the project-specific guides below before changing inputs, operating modes or deployment assumptions.

### Usage and operations

- [CONTINUITY REVIEW](CONTINUITY_REVIEW.md)
- [RELEASE](RELEASE.md)
- [USER GUIDE](USER_GUIDE.md)
- [releases/v1.1.0](releases/v1.1.0.md)

### Design and contracts

- [API](API.md)
- [ARCHITECTURE](ARCHITECTURE.md)
- [MODEL](MODEL.md)

### Security and validation

- [VALIDATION](VALIDATION.md)

## Historical results and reproduction

The reviewed source is [`97f729a525aab8c9388c24db26748c475c88d82d`](https://github.com/JasonStys/ccsds-telemetry-integrity-lab/tree/97f729a525aab8c9388c24db26748c475c88d82d). The observed functional workflow baseline is `97f729a525aab8c9388c24db26748c475c88d82d`; those observations are recorded at `2026-11-10T05:25:40.628667+00:00`. They do not certify an unrun later revision.

- [Detailed recorded validation](reports/PORTABLE_REFRESH_20261109.md)
- [Current Actions](https://github.com/JasonStys/ccsds-telemetry-integrity-lab/actions) records later integration checks separately.
- Preserve dated measurements and follow the existing testing guide to reproduce them; a test-source inventory alone does not establish execution.

## Practical boundaries

- Restricted record-delimited educational CCSDS profile; no live radio/spacecraft integration, raw byte-stream resynchronization or payload authentication.
- Timeline segments are review boundaries, not proof of true sender sessions; provisional recovery does not establish permanent packet loss.
- Unsigned desktop portable folders, not system installers or clean-machine proof. Three-OS extracted-native checks drive an owned URL; default OS browser opening remains manual.

## Maintaining these editions

Update the editable usage/design/test documents first. Rebuild and visually review every Word page and workbook tab before replacing an edition; verify the exact binary digests and evidence source in publications.json. Keep account data, logs with secrets, installed-app state and private test stores out of documentation. Source and release assets retain their existing security and licensing boundaries.
