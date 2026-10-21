# Packet profile and continuity semantics

By Jason Stys. This document separates the standards-derived header layout from original local policy. Nothing here implements a complete protocol service or operational space link.

## Normative baseline and restricted scope

The reference is official [CCSDS 133.0-B-2, June 2020, EC2 distribution](https://ccsds.org/Pubs/133x0b2e2.pdf), especially §4.1.2–4.1.4. Primary-header layout, MSB-first order, encoded data length, idle APID and counter modulus follow that source. The [CCSDS publication catalog](https://ccsds.org/publications/sls/) identifies the publication. Accessed 2026-10-20.

| Header bits | Width | Meaning                    |
| ----------- | ----- | -------------------------- |
| 0–2         | 3     | Version                    |
| 3           | 1     | Packet type                |
| 4           | 1     | Secondary-header indicator |
| 5–15        | 11    | APID                       |
| 16–17       | 2     | Sequence flags             |
| 18–31       | 14    | Sequence count             |
| 32–47       | 16    | Encoded data length        |

This lab accepts version zero, telemetry type zero, secondary indicator zero and unsegmented flags `11`. Encoded length `C` represents `C+1` data octets, so expected total is `C+7`. Counter modulus is 16384. APID 2047 identifies idle. Those facts do **not** establish full protocol conformance. A valid variant can be outside this lab's restricted profile. The source document is linked, not redistributed or copied into the repository.

## Original lab envelope and policy

The supported local payload limit is 32, 128 or 4096 bytes; the standard's wider length representation is decoded without wrapping but is not fully accepted by this implementation. `65535` is interpreted as 65536 data bytes, not zero. The primary six bytes are decoded only after checking their presence. Rust uses checked safe slices and explicit endian conversion, with no struct casts, unsafe code or external crates.

Input is **ASCII text with one hex record per newline**, not a standardized space-link transfer frame. The whole envelope is capped at 131072 bytes and 128 records. A line longer than 8204 characters is rejected as record-too-large before hex allocation. Internal blank lines are zero-byte records and therefore truncated headers. A final newline is a terminator, not an extra record. CRLF is accepted and normalized. Odd lengths, spaces and nonhex characters produce invalid-hex records. Non-ASCII input, excessive record count or whole-envelope oversize reject the entire capture.

These supplied boundaries are why a bad declared length cannot consume the next record. There is **no raw-byte resynchronization scanner**, magic-marker inference, blind skip-a-byte recovery or guarantee of recovering packet boundaries after link corruption. Concatenated packets without a newline are one invalid record, not silently repaired. This avoids presenting guessed framing as verified data.

Validation precedence is deterministic: record size/hex decoding; truncated primary header; profile-limit validity; version; exact actual/declared length; local payload cap; type; secondary indicator; segmentation. Header fields remain inspectable on later rejection. Accepted payload bytes remain opaque. No payload schema, timestamp, calibration, science units, secondary header, fragmentation/reassembly, TM/AOS/USLP frame, CRC, error correction, encryption or authentication is inferred or implemented.

## Receipt-time continuity review

Within **one explicit capture/session**, keep a baseline count and accepted payload for each non-idle APID. There is no assumption of global APID uniqueness across spacecraft or sessions; do not combine sources. Only supported accepted non-idle records enter this state.

Let `d = (received_count − baseline_count) mod 16384`, with forward window `w ∈ {16,256,8191}`:

| Condition                | Disposition                                  | Advance baseline? |
| ------------------------ | -------------------------------------------- | ----------------- |
| No prior baseline        | first                                        | Yes               |
| Idle APID                | idle                                         | No                |
| `d=0`, same payload      | repeat-of-baseline                           | No                |
| `d=0`, different payload | counter-reuse                                | No                |
| `d=1`                    | in-order                                     | Yes               |
| `2≤d≤w`                  | gap, `d−1` values unobserved at this receipt | Yes               |
| `w<d<8192`               | forward-jump-review                          | No                |
| `d=8192`                 | ambiguous-half-range                         | No                |
| `d>8192`                 | late-or-reset                                | No                |
| Rejected record          | rejected                                     | No                |

“Review” covers repeats, reuse, gaps and all ambiguous ordering outcomes. Structurally accepted, needs review and idle are overlapping dimensions—not three mutually exclusive packet classes. The accepted total includes idle/review; rejected is its complement. Review never silently drops a record or commands an operational action.

**`unobserved_values` is an event observation, not a reconciled inventory of permanently missing packets.** A delayed record can arrive afterward; rejected records may expose those counts; a full unseen wrap or sender reset is possible. Summed values count receipt-time gap events and can overlap; they are not unique or unrecovered loss totals. We do not maintain/reconcile a missing-packet set. Repeat-of-baseline is not a global replay detector; full-wrap ambiguity, prior repeats not matching the baseline, reset history and time ordering require context absent here.

The forward window is an original review policy, not a CCSDS-mandated loss classifier. Its narrow setting withholds large jumps instead of asserting forward loss. Non-advancement on ambiguous/late/reused input protects baseline monotonicity under the assumed session but cannot prove the sender's true history.

## Content integrity and evidence

The payload-corruption fixture changes one data byte while preserving header/length. Both Rust and Python accept it. This is expected: this implementation verifies **structure, not payload correctness or sender authenticity**. No packet CRC is invented and represented as CCSDS. Any operational integrity layer must come from the actual mission/link/application specification and independent assurance, not this toy profile.

The report SHA-256 hashes canonical evidence, excluding its self-ID. Record hashes identify normalized hex text, not signed packets; uppercase/lowercase hex normalizes. Full input, settings, parser outputs, state decisions, scope and provenance are retained. Wall clock, machine path and runtime measurements are excluded for cross-platform reproducibility. Imported provenance is local-hex rather than synthetic; identical raw packets can therefore yield different full report hashes across those source categories.

## Complexity and scientific limits

For total capture characters `B` and records `R`, hex parsing/reference comparison/report assembly are linear `O(B+R)` with average constant-time per-APID dictionary access; APID space is bounded. The Rust `inspect` returns a borrowed accepted payload; text decoding/JSON/IPC still allocate. Memory is `O(B+R+A)` for bounded input, evidence and at most `A≤R` active APIDs. There is no end-to-end zero-copy or hard-real-time claim. Always comparing two implementations adds processing/IPC overhead intentionally for inspectability, not production throughput.

No hardware/clock, data-rate, operational latency or physical prediction is modeled. Synthetic captures and independently checked field arithmetic provide software verification, not validation against a mission's actual telemetry schema. The application is not a PICS declaration or certification. See [validation](VALIDATION.md) for actual tests and gaps.
