"""Independent native/reference contracts and stateful edge cases by Jason Stys.

Functions: test contracts for raw bytes, field boundaries, continuity and input limits.
Variables: bounded captures, synthetic fields and corrupted bytes. Lines: docs/CODE_INDEX.md.
These tests execute the real Rust release worker, not mocked parser success.
"""

import json
import struct
import subprocess
from itertools import product

import pytest
from hypothesis import given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

from packetlab.engine import (
    CHOICES,
    SCENARIOS,
    Settings,
    analyze,
    build_import,
    build_run,
    fixture,
    packet,
)
from packetlab.native import executable, inspect_capture
from packetlab.reference import MAX_CAPTURE, capture_lines, inspect_record


@pytest.mark.parametrize("values", list(product(SCENARIOS, *CHOICES.values())))
def test_complete_grid(values):
    """All 108 configurations agree cross-language, repeat identically and account for every record."""
    scenario, cap, window = values
    run = build_run(Settings(scenario, cap, window))
    assert run == build_run(Settings(scenario, cap, window))
    totals = run["totals"]
    assert totals["records"] == totals["accepted"] + totals["rejected"] == len(run["rows"])
    assert totals["review"] <= totals["accepted"]
    assert all(
        not row["baseline_advanced"]
        for row in run["rows"]
        if row["code"] != "accepted" or row["disposition"] == "idle"
    )


@given(st.lists(st.binary(min_size=0, max_size=512), max_size=15))
@hypothesis_settings(max_examples=100, deadline=None, derandomize=True)
def test_arbitrary_byte_records(records):
    """Arbitrary bytes have identical Rust and independent Python structural results."""
    lines = [record.hex() for record in records]
    text = "\n".join(lines) + ("\n" if lines else "")
    assert inspect_capture(text, 128) == [inspect_record(line, 128) for line in lines]


@given(
    st.integers(0, 2047),
    st.integers(0, 16383),
    st.binary(min_size=1, max_size=4096),
    st.integers(0, 3),
)
@hypothesis_settings(max_examples=100, deadline=None, derandomize=True)
def test_constructed_fields(apid, count, payload, flags):
    """Independent test packing covers valid bodies and unsupported segmentation, not just random rejects."""
    text = (struct.pack(">HHH", apid, flags * 16384 + count, len(payload) - 1) + payload).hex()
    native = inspect_capture(text, 4096)[0]
    assert native == inspect_record(text, 4096)
    assert native["header"]["apid"] == apid and native["header"]["sequence"] == count
    assert native["code"] == ("accepted" if flags == 3 else "unsupported-segmentation")
    if flags == 3:
        assert native["payload_hex"] == payload.hex()


def test_manually_reviewed_golden():
    """Known header does not depend on production fixture encoding for expected field values."""
    actual = inspect_capture("002ac0010002deadbe\n", 128)[0]
    assert actual == {
        "code": "accepted",
        "header": {
            "version": 0,
            "packet_type": 0,
            "secondary": 0,
            "apid": 42,
            "flags": 3,
            "sequence": 1,
            "data_length": 2,
            "expected_size": 9,
        },
        "actual_size": 9,
        "payload_hex": "deadbe",
    }


@pytest.mark.parametrize(
    "scenario,expected",
    [
        ("sequence-gap", ["first", "in-order", "gap", "in-order"]),
        ("wraparound", ["first", "in-order", "in-order", "in-order"]),
        ("duplicate-and-reuse", ["first", "repeat-of-baseline", "counter-reuse", "in-order"]),
        ("out-of-order", ["first", "gap", "late-or-reset", "in-order"]),
        ("ambiguous-jump", ["first", "ambiguous-half-range", "in-order"]),
        ("idle-and-recovery", ["first", "idle", "first", "idle", "in-order", "in-order"]),
    ],
)
def test_continuity_dispositions(scenario, expected):
    """Rejected/delayed/ambiguous/duplicate records never roll the accepted high-water mark backward."""
    run = build_run(Settings(scenario=scenario))
    assert [row["disposition"] for row in run["rows"]] == expected
    if scenario == "sequence-gap":
        assert run["totals"]["unobserved_values"] == 3


def test_forward_window_is_a_review_policy():
    """A larger forward jump is held for review under a narrow policy, not declared definite loss."""
    text = packet(42, 0) + "\n" + packet(42, 20) + "\n" + packet(42, 1)
    narrow = analyze(text, Settings(forward_window=16), "local-hex")
    wide = analyze(text, Settings(forward_window=256), "local-hex")
    assert [row["disposition"] for row in narrow["rows"]] == [
        "first",
        "forward-jump-review",
        "in-order",
    ]
    assert [row["disposition"] for row in wide["rows"]] == ["first", "gap", "late-or-reset"]
    assert narrow["totals"]["unobserved_values"] == 0


def test_declared_length_does_not_swallow_the_next_record():
    """Lab record isolation permits recovery; concatenation without a boundary is not silently repaired."""
    run = build_run(Settings(scenario="truncated-and-length"))
    assert [row["code"] for row in run["rows"]] == [
        "truncated-header",
        "length-mismatch",
        "accepted",
        "invalid-hex",
        "accepted",
    ]
    assert inspect_capture(packet(42, 0) + packet(42, 1), 128)[0]["code"] == "length-mismatch"


def test_corruption_is_not_falsely_detected():
    """Payload mutation can pass all structural checks; report explicitly refuses integrity/authenticity claims."""
    run = build_run(Settings(scenario="payload-corruption"))
    assert run["totals"]["accepted"] == 3 and run["totals"]["review"] == 0
    assert run["rows"][0]["payload_hex"] != run["rows"][1]["payload_hex"]
    assert "cannot" in SCENARIOS["payload-corruption"] and "no payload checksum" in run["note"]


@pytest.mark.parametrize(
    "text,code",
    [
        ("", "truncated-header"),
        ("0", "invalid-hex"),
        ("xx", "invalid-hex"),
        ("00 00", "invalid-hex"),
        ("=FORMULA", "invalid-hex"),
        ("00" * 4103, "record-too-large"),
    ],
    ids=["empty", "odd", "nonhex", "space", "formula", "oversized-record"],
)
def test_per_record_errors(text, code):
    """Malformed text is an explicit record error; data are never evaluated or coerced."""
    rows = inspect_capture(text + "\n", 128)
    assert rows[0]["code"] == code


@pytest.mark.parametrize(
    "text", ["a" * (MAX_CAPTURE + 1), "00\n" * 129, "é"], ids=["size", "count", "ascii"]
)
def test_capture_rejection(text):
    """Envelope failures reject the whole input before any worker evidence is used."""
    with pytest.raises(ValueError):
        capture_lines(text)


@pytest.mark.parametrize(
    "arguments,data",
    [
        ([], b""),
        (["bad"], b""),
        (["0"], b""),
        (["128"], b"\xff"),
        (["128"], b"a" * (MAX_CAPTURE + 1)),
        (["128"], b"00\n" * 129),
    ],
    ids=["args", "nonnumeric", "limit", "encoding", "size", "count"],
)
def test_actual_worker_envelope_failures(arguments, data):
    """The native CLI itself enforces bounds, not only the Python front door."""
    result = subprocess.run(
        [str(executable()), *arguments], input=data, capture_output=True, timeout=5
    )
    assert result.returncode == 2 and result.stdout == b"" and b"panic" not in result.stderr


def test_crlf_empty_and_import(tmp_path):
    """CRLF normalizes deterministically; imported source remains distinct in provenance."""
    text = fixture("nominal")
    assert inspect_capture(text.replace("\n", "\r\n"), 128) == inspect_capture(text, 128)
    assert build_run(Settings(scenario="empty-capture"))["totals"]["records"] == 0
    path = tmp_path / "capture.hex"
    path.write_bytes(text.encode())
    imported = build_import(path, Settings())
    assert imported["scenario"] == "local-hex" and imported["rows"] == build_run(Settings())["rows"]
    path.write_bytes(b"x" * (MAX_CAPTURE + 1))
    with pytest.raises(ValueError):
        build_import(path, Settings())
    path.write_bytes(b"\xff")
    with pytest.raises(ValueError):
        build_import(path, Settings())


@pytest.mark.parametrize(
    "key,value",
    [
        ("payload_limit", True),
        ("payload_limit", 128.0),
        ("payload_limit", 1),
        ("forward_window", 8192),
        ("scenario", []),
        ("scenario", "unknown"),
    ],
)
def test_setting_rejections(key, value):
    """Finite strict settings cannot be widened by a boolean, string, float or unknown fixture."""
    with pytest.raises(ValueError):
        Settings(**{key: value})


def test_native_bridge_failure_paths(monkeypatch, tmp_path):
    """A missing, failing, oversized or malformed worker never triggers a fake Python fallback."""
    monkeypatch.setattr("packetlab.native.executable", lambda: tmp_path / "missing")
    with pytest.raises(RuntimeError, match="missing"):
        inspect_capture("", 128)
    monkeypatch.setattr("packetlab.native.executable", lambda: tmp_path)
    with pytest.raises(ValueError):
        inspect_capture("", False)
    worker = tmp_path / "worker"
    worker.touch()
    monkeypatch.setattr("packetlab.native.executable", lambda: worker)
    for output in (b"not JSON", b"{}\n", b"x" * 1_048_577, b""):
        monkeypatch.setattr(
            "packetlab.native.subprocess.run",
            lambda *a, output=output, **k: subprocess.CompletedProcess([], 0, output, b""),
        )
        with pytest.raises(RuntimeError):
            inspect_capture("00\n", 128)


def test_disagreement_withholds_evidence(monkeypatch):
    """The actual cross-language comparison is a gate, not an always-green display label."""
    monkeypatch.setattr("packetlab.engine.inspect_capture", lambda *args: [])
    with pytest.raises(RuntimeError, match="disagreement"):
        build_run(Settings())


def test_fixture_rejection():
    """Synthetic constructor rejects impossible field widths and empty data."""
    with pytest.raises(ValueError):
        fixture("missing")
    with pytest.raises(ValueError):
        packet(2048, 0)
    with pytest.raises(ValueError):
        packet(42, 0, b"")
    assert json.loads(json.dumps(build_run(Settings())))["version"] == "1.0.0"
