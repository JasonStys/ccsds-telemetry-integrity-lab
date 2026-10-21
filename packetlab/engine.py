"""Synthetic captures, continuity review and canonical evidence by Jason Stys.

Functions: packet, fixture, analyze, build_run, build_import, catalog, run_id.
Variables: finite settings, per-APID high-water state and independent reference rows.
Exact locations: docs/CODE_INDEX.md. Sequence heuristics do not establish packet authenticity.
"""

import hashlib
import json
import struct
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from packetlab.native import inspect_capture
from packetlab.reference import MAX_CAPTURE, capture_lines, inspect_record

CHOICES = {"payload_limit": (32, 128, 4096), "forward_window": (16, 256, 8191)}
SCENARIOS = {
    "nominal": "Interleaved clean telemetry",
    "sequence-gap": "Missing sequence values",
    "wraparound": "Counter wraps at 16384",
    "duplicate-and-reuse": "Repeat vs counter reuse",
    "out-of-order": "Delayed record after a gap",
    "ambiguous-jump": "Half-range ambiguity",
    "truncated-and-length": "Truncation with record recovery",
    "unsupported-profile": "Outside the supported profile",
    "payload-limit": "Declared payload exceeds local cap",
    "payload-corruption": "A bit flip the header cannot detect",
    "idle-and-recovery": "Idle and independent APID streams",
    "empty-capture": "No records supplied",
}
NOTES = {
    "payload-corruption": "A seeded payload byte is changed. All headers remain valid. This profile has no payload checksum: acceptance does not establish content integrity or authenticity.",
    "truncated-and-length": "Later records recover only because the lab capture supplies independent newline boundaries. Raw CCSDS byte-stream resynchronization is not implemented.",
    "ambiguous-jump": "A jump of half the 14-bit counter range cannot be ordered without external session/time information. It does not advance the baseline.",
}


@dataclass(frozen=True, slots=True)
class Settings:
    """Finite reviewed profile and continuity preferences; not mission protocol management."""

    scenario: str = "nominal"
    payload_limit: int = 128
    forward_window: int = 256

    def __post_init__(self) -> None:
        """Reject coercion, bools and unknown options."""
        if not isinstance(self.scenario, str) or self.scenario not in SCENARIOS:
            raise ValueError("Unknown scenario")
        for key, choices in CHOICES.items():
            value = getattr(self, key)
            if type(value) is not int or value not in choices:
                raise ValueError("Unsupported setting")


def packet(
    apid: int,
    count: int,
    payload: bytes = b"\x10\x20\x30\x40",
    flags: int = 3,
    identification: int = 0,
) -> str:
    """Construct invented fixtures only, not an uplink/send API or operational packet service."""
    if not (
        0 <= apid <= 2047
        and 0 <= count <= 16383
        and 0 <= flags <= 3
        and 1 <= len(payload) <= 4096
        and identification in (0, 0x0800, 0x1000, 0x2000)
    ):
        raise ValueError("Invalid synthetic packet fields")
    return (
        struct.pack(">HHH", identification | apid, (flags << 14) | count, len(payload) - 1)
        + payload
    ).hex()


def fixture(scenario: str) -> str:
    """Return fully invented hex records with trusted lab boundaries and no live source data."""
    match scenario:
        case "nominal":
            rows = [packet(42, 0), packet(100, 8), packet(42, 1), packet(100, 9), packet(42, 2)]
        case "sequence-gap":
            rows = [packet(42, count) for count in (10, 11, 15, 16)]
        case "wraparound":
            rows = [packet(42, count) for count in (16382, 16383, 0, 1)]
        case "duplicate-and-reuse":
            rows = [packet(42, 10), packet(42, 10), packet(42, 10, b"DIFF"), packet(42, 11)]
        case "out-of-order":
            rows = [packet(42, count) for count in (50, 52, 51, 53)]
        case "ambiguous-jump":
            rows = [packet(42, count) for count in (0, 8192, 1)]
        case "truncated-and-length":
            rows = ["002ac00000", "002ac001000a11", packet(42, 2), "=FORMULA", packet(42, 3)]
        case "unsupported-profile":
            rows = (
                [packet(42, 0, identification=word) for word in (0x2000, 0x1000, 0x0800)]
                + [packet(42, 0, flags=flag) for flag in range(3)]
                + [packet(42, 0)]
            )
        case "payload-limit":
            rows = [packet(42, 0, bytes(range(256)) + bytes(range(44))), packet(42, 1)]
        case "payload-corruption":
            rows = [packet(42, 0), packet(42, 1, b"\x10\x21\x30\x40"), packet(42, 2)]
        case "idle-and-recovery":
            rows = [
                packet(42, 0),
                packet(2047, 100, b"\x55"),
                packet(100, 8),
                packet(2047, 7, b"\xaa"),
                packet(42, 1),
                packet(100, 9),
            ]
        case "empty-capture":
            rows = []
        case _:
            raise ValueError("Unknown fixture")
    return "\n".join(rows) + ("\n" if rows else "")


def canonical(data: dict[str, Any]) -> bytes:
    """Stable machine-independent evidence encoding without timestamps or machine paths."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def run_id(data: dict[str, Any]) -> str:
    """Content-address all evidence except its self-referential identifier; not a signature."""
    return hashlib.sha256(
        canonical({key: value for key, value in data.items() if key != "id"})
    ).hexdigest()


def analyze(text: str, settings: Settings, source: str) -> dict[str, Any]:
    """Compare actual Rust results to independent Python, then review per-APID continuity."""
    lines = capture_lines(text)
    native = inspect_capture(text, settings.payload_limit)
    reference = [inspect_record(line, settings.payload_limit) for line in lines]
    if native != reference:
        raise RuntimeError("Independent parser disagreement; evidence withheld")
    previous: dict[int, tuple[int, str]] = {}
    rows = []
    for index, (line, result) in enumerate(zip(lines, native, strict=True)):
        disposition, gap, advance = "rejected", 0, False
        header = result["header"]
        if result["code"] == "accepted":
            apid, count = header["apid"], header["sequence"]
            if apid == 2047:
                disposition = "idle"
            elif apid not in previous:
                disposition, advance = "first", True
            else:
                last, last_payload = previous[apid]
                delta = (count - last) % 16384
                if delta == 0:
                    disposition = (
                        "repeat-of-baseline"
                        if result["payload_hex"] == last_payload
                        else "counter-reuse"
                    )
                elif delta == 1:
                    disposition, advance = "in-order", True
                elif delta <= settings.forward_window:
                    disposition, gap, advance = "gap", delta - 1, True
                elif delta < 8192:
                    disposition = "forward-jump-review"
                elif delta == 8192:
                    disposition = "ambiguous-half-range"
                else:
                    disposition = "late-or-reset"
            if advance:
                previous[apid] = (count, result["payload_hex"])
        review = disposition in {
            "gap",
            "counter-reuse",
            "repeat-of-baseline",
            "forward-jump-review",
            "ambiguous-half-range",
            "late-or-reset",
        }
        rows.append(
            {
                **result,
                "index": index,
                "raw_hex": line,
                "disposition": disposition,
                "unobserved_values": gap,
                "baseline_advanced": advance,
                "review": review,
                "record_sha256": hashlib.sha256(line.lower().encode()).hexdigest(),
            }
        )
    result = {
        "version": "1.0.0",
        "scenario": source,
        "settings": {
            "payload_limit": settings.payload_limit,
            "forward_window": settings.forward_window,
        },
        "capture": "\n".join(lines) + ("\n" if lines else ""),
        "rows": rows,
        "totals": {
            "records": len(rows),
            "accepted": sum(row["code"] == "accepted" for row in rows),
            "rejected": sum(row["code"] != "accepted" for row in rows),
            "review": sum(row["review"] for row in rows),
            "idle": sum(row["disposition"] == "idle" for row in rows),
            "unobserved_values": sum(row["unobserved_values"] for row in rows),
        },
        "note": NOTES.get(
            source,
            "Single capture/session, ordered lab records. Sequence heuristics cannot distinguish all loss, reordering, replay, resets or full counter cycles.",
        ),
        "provenance": {
            "author": "Jason Stys",
            "format": "CCSDS 133.0-B-2 restricted telemetry profile",
            "source": "explicit local ASCII hex capture"
            if source == "local-hex"
            else "synthetic fixtures",
            "parser": "safe Rust 1.98.1, zero external crates",
            "reference": "independent Python quotient/remainder parser; all rows agree",
            "payload_integrity": "not established: no mandatory payload checksum in this packet profile",
            "scope": "Offline educational record validation; not a complete CCSDS entity or operational ground system",
        },
    }
    result["id"] = run_id(result)
    return result


def build_run(settings: Settings) -> dict[str, Any]:
    """Run a reviewed fixture with the real native parser, never a simulated worker result."""
    return analyze(fixture(settings.scenario), settings, settings.scenario)


def build_import(path: Path, settings: Settings) -> dict[str, Any]:
    """Read a bounded explicit local capture; no upload/remote fetch or arbitrary execution."""
    with path.open("rb") as source:
        data = source.read(MAX_CAPTURE + 1)
    if len(data) > MAX_CAPTURE:
        raise ValueError("Capture exceeds 128 KiB")
    try:
        text = data.decode("ascii")
    except UnicodeError as error:
        raise ValueError("Capture must contain ASCII hex records") from error
    return analyze(text, settings, "local-hex")


def catalog() -> dict[str, Any]:
    """Publish finite controls and supported profile without exposing paths or arbitrary files."""
    return {"scenarios": SCENARIOS, "choices": CHOICES, "defaults": asdict(Settings())}
