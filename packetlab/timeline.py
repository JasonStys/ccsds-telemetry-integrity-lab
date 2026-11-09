"""Conservative APID continuity timelines by Jason Stys.

Function: timelines. Variables: per-APID anchors, compressed gap intervals and observed recoveries.
No original decision is rewritten and no permanent loss is inferred. Lines: docs/CODE_INDEX.md.
"""

from typing import Any


def timelines(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Track provisional gaps within review segments; ambiguous observations break reconciliation.

    Missing ranges are compressed, so memory is O(records + recoveries), not O(counter gaps).
    A late accepted counter can recover one uniquely matching range in the current segment.
    Payload equality/authenticity and true sender sessions remain unknown; segments are review
    boundaries, not assertions that a spacecraft restarted. Rejected and idle records never anchor.
    """
    streams: dict[int, dict[str, Any]] = {}
    for row in rows:
        header = row["header"]
        if row["code"] != "accepted" or header["apid"] == 2047:
            continue
        apid, sequence = header["apid"], header["sequence"]
        stream = streams.setdefault(
            apid, {"apid": apid, "segment": 0, "anchored": False, "gaps": [], "events": []}
        )
        disposition = row["disposition"]
        event: dict[str, Any] = {
            "record": row["index"],
            "sequence": sequence,
            "original_decision": disposition,
            "kind": disposition,
            "segment": stream["segment"],
        }
        if row["baseline_advanced"]:
            if disposition == "gap" and stream["anchored"]:
                count = row["unobserved_values"]
                stream["gaps"].append(
                    {
                        "origin_record": row["index"],
                        "segment": stream["segment"],
                        "first_sequence": (sequence - count) % 16384,
                        "count": count,
                        "recoveries": [],
                        "ambiguous": False,
                    }
                )
            elif not stream["anchored"]:
                event["kind"] = "review-segment-anchor"
            stream["anchored"] = True
        elif disposition == "late-or-reset":
            matching = [
                gap
                for gap in stream["gaps"]
                if gap["segment"] == stream["segment"]
                and not gap["ambiguous"]
                and (sequence - gap["first_sequence"]) % 16384 < gap["count"]
            ]
            pending = [
                gap
                for gap in matching
                if sequence not in {entry["sequence"] for entry in gap["recoveries"]}
            ]
            if len(pending) == 1:
                pending[0]["recoveries"].append({"sequence": sequence, "record": row["index"]})
                event["kind"] = "provisional-gap-recovery"
                event["gap_origin_record"] = pending[0]["origin_record"]
            elif matching and not pending:
                event["kind"] = "repeat-of-recovery"
            else:
                event["kind"] = "ambiguity-boundary"
        elif disposition in {"forward-jump-review", "ambiguous-half-range", "counter-reuse"}:
            event["kind"] = "ambiguity-boundary"
        if event["kind"] == "ambiguity-boundary":
            for gap in stream["gaps"]:
                if gap["segment"] == stream["segment"] and len(gap["recoveries"]) < gap["count"]:
                    gap["ambiguous"] = True
            stream["segment"] += 1
            stream["anchored"] = False
        stream["events"].append(event)
    result = []
    for apid in sorted(streams):
        stream = streams[apid]
        for gap in stream["gaps"]:
            gap["remaining"] = gap["count"] - len(gap["recoveries"])
            gap["status"] = (
                "ambiguous"
                if gap["ambiguous"]
                else "provisional"
                if gap["remaining"]
                else "recovered"
            )
        result.append(
            {
                "apid": apid,
                "events": stream["events"],
                "gaps": stream["gaps"],
                "provisional_total": sum(gap["count"] for gap in stream["gaps"]),
                "recovered": sum(len(gap["recoveries"]) for gap in stream["gaps"]),
                "outstanding": sum(
                    gap["remaining"] for gap in stream["gaps"] if not gap["ambiguous"]
                ),
                "uncertain": sum(gap["remaining"] for gap in stream["gaps"] if gap["ambiguous"]),
            }
        )
    return result
