"""Independent sequence-recovery traces by Jason Stys.

Functions: capture and test_*; variables: hand-computed wrap/gap/late counters and APID streams.
All integration cases execute the real unchanged native parser. Lines: docs/CODE_INDEX.md.
"""

from packetlab.engine import Settings, analyze, packet, run_id
from packetlab.timeline import timelines


def capture(counts: list[int]) -> dict:
    """Run one accepted APID stream with opaque synthetic bytes and explicit record boundaries."""
    return analyze("\n".join(packet(42, count) for count in counts), Settings(), "local-hex")


def test_wrap_recovery_duplicate_preserves_original_decisions():
    """Missing 16383 and 0 recover late exactly once despite a duplicate late packet."""
    run = capture([16382, 1, 16383, 0, 0, 2])
    stream = run["apid_timelines"][0]
    assert (
        stream["provisional_total"],
        stream["recovered"],
        stream["outstanding"],
        stream["uncertain"],
    ) == (2, 2, 0, 0)
    assert stream["gaps"][0]["first_sequence"] == 16383
    assert stream["gaps"][0]["status"] == "recovered"
    assert [row["disposition"] for row in run["rows"]] == [
        "first",
        "gap",
        "late-or-reset",
        "late-or-reset",
        "late-or-reset",
        "in-order",
    ]
    assert run["totals"]["unobserved_values"] == 2
    assert stream["events"][4]["kind"] == "repeat-of-recovery"
    assert run["id"] == run_id(run)


def test_ambiguity_boundaries_do_not_claim_late_recovery():
    """Half-range, reuse and unknown late/reset cannot reconcile across a review boundary."""
    for counts in ([10, 13, 8205, 11, 14], [10, 13, 9, 11, 14]):
        run = capture(list(counts))
        stream = run["apid_timelines"][0]
        assert stream["uncertain"] == 2
        assert stream["recovered"] == 0
        assert stream["gaps"][0]["status"] == "ambiguous"
        assert stream["events"][2]["kind"] == "ambiguity-boundary"
    run = analyze(
        "\n".join([packet(42, 10), packet(42, 13), packet(42, 13, payload=b"x"), packet(42, 14)]),
        Settings(),
        "local-hex",
    )
    assert run["apid_timelines"][0]["uncertain"] == 2


def test_idle_rejected_and_other_apid_are_isolated():
    """Neither idle, rejected, nor a different APID fills APID42's missing value."""
    run = analyze(
        "\n".join(
            [packet(42, 10), packet(42, 12), packet(43, 11), packet(2047, 11), "00", packet(42, 11)]
        ),
        Settings(),
        "local-hex",
    )
    assert [s["apid"] for s in run["apid_timelines"]] == [42, 43]
    assert run["apid_timelines"][0]["gaps"][0]["recoveries"] == [{"sequence": 11, "record": 5}]
    assert timelines([]) == []


def test_maximum_gap_stays_compressed():
    """The widest reviewed forward gap stores one interval rather than thousands of values."""
    run = analyze(
        "\n".join([packet(42, 0), packet(42, 8191)]), Settings(forward_window=8191), "local-hex"
    )
    stream = run["apid_timelines"][0]
    assert len(stream["gaps"]) == 1
    assert stream["outstanding"] == 8190
    assert stream["gaps"][0]["recoveries"] == []
