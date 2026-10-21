"""Inert portable exports and explicit immutable SQL history by Jason Stys.

Functions: export_report, save_history. Variables: bounded evidence, record rows,
hashes and parameterized database values. Locations: docs/CODE_INDEX.md.
Imported text never enters CSV cells or executable markup. Persistence is CLI opt-in.
"""

import csv
import html
import io
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from packetlab.engine import canonical, run_id


def export_report(run: dict[str, Any], format_name: str) -> tuple[bytes, str]:
    """Export complete evidence/source; CSV intentionally excludes raw imported text."""
    if format_name == "input":
        return run["capture"].encode("ascii"), "text/plain"
    if format_name == "json":
        return json.dumps(
            run, indent=2, sort_keys=True, allow_nan=False
        ).encode() + b"\n", "application/json"
    if format_name == "csv":
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            (
                "index",
                "code",
                "apid",
                "sequence",
                "actual_size",
                "expected_size",
                "disposition",
                "unobserved_values",
                "baseline_advanced",
                "record_sha256",
            )
        )
        for row in run["rows"]:
            header = row["header"] or {}
            writer.writerow(
                (
                    row["index"],
                    row["code"],
                    header.get("apid"),
                    header.get("sequence"),
                    row["actual_size"],
                    header.get("expected_size"),
                    row["disposition"],
                    row["unobserved_values"],
                    row["baseline_advanced"],
                    row["record_sha256"],
                )
            )
        return output.getvalue().encode(), "text/csv"
    if format_name == "html":
        body = html.escape(json.dumps(run, indent=2, sort_keys=True, allow_nan=False))
        document = (
            '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src &apos;none&apos;; base-uri &apos;none&apos;; form-action &apos;none&apos;"><title>Telemetry evidence — Jason Stys</title><h1>Telemetry integrity evidence</h1><p>By Jason Stys. Structural validation does not establish payload integrity or authenticity. Offline synthetic record lab, not operational telemetry assurance.</p><pre>'
            + body
            + "</pre></html>"
        )
        return document.encode(), "text/html"
    raise ValueError("Unsupported report format")


def save_history(path: Path, run: dict[str, Any]) -> None:
    """Verify SHA, deduplicate and cap history without replacing, updating or deleting rows."""
    if run.get("id") != run_id(run):
        raise ValueError("Evidence hash does not match its contents")
    schema = Path(__file__).with_name("resources") / "history.sql"
    with closing(sqlite3.connect(path, timeout=5)) as connection, connection:
        connection.executescript(schema.read_text(encoding="utf-8"))
        connection.execute("BEGIN IMMEDIATE")
        previous = connection.execute(
            "SELECT report_json FROM runs WHERE id = ?", (run["id"],)
        ).fetchone()
        encoded = canonical(run).decode()
        if previous:
            if previous[0] != encoded:
                raise ValueError("History identifier collision")
            return
        if connection.execute("SELECT count(*) FROM runs").fetchone()[0] >= 100:
            raise ValueError("History is full; choose a new explicit local database")
        connection.execute(
            "INSERT INTO runs(id, scenario, report_json) VALUES(?, ?, ?)",
            (run["id"], run["scenario"], encoded),
        )
