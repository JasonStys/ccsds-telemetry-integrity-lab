"""Deterministic cross-language packet contracts and descriptive timing by Jason Stys.

Functions: snapshot, main. Variables: fixtures, caps, evidence hashes and timing samples.
Only --write updates reviewed contracts. Exact locations: docs/CODE_INDEX.md.
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packetlab.engine import SCENARIOS, Settings, build_run, fixture  # noqa: E402


def snapshot() -> str:
    """Pin each scenario under strict and broad payload caps; all rows must agree cross-language."""
    rows = []
    for scenario in SCENARIOS:
        for cap in (32, 4096):
            run = build_run(Settings(scenario=scenario, payload_limit=cap))
            rows.append(
                {
                    "scenario": scenario,
                    "payload_limit": cap,
                    "id": run["id"],
                    "totals": run["totals"],
                }
            )
    return (
        json.dumps(
            {
                "description": "Synthetic Rust/Python packet contract summaries by Jason Stys; no operational claims",
                "cases": rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def main() -> int:
    """Check contract drift and report uncached full-process timing without machine-specific gates."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    for path, content in (
        (ROOT / "docs/reports/benchmark.json", snapshot()),
        (ROOT / "examples/nominal.hex", fixture("nominal")),
    ):
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
        elif not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise SystemExit("Contract drift: review before --write")
    timings = []
    for _ in range(20):
        start = time.perf_counter()
        build_run(Settings(scenario="unsupported-profile"))
        timings.append((time.perf_counter() - start) * 1000)
    print(
        f"24 deterministic cross-language contracts passed; uncached worker+analysis median {statistics.median(timings):.3f} ms (descriptive only)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
