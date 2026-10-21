"""Fixed trusted-worker bridge by Jason Stys.

Functions: executable, inspect_capture. Variables: bounded capture bytes, fixed native
path, timeout and checked JSON rows. Exact locations: docs/CODE_INDEX.md.
Never uses a shell, caller executable/path argument or Python parser fallback.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from packetlab.reference import capture_lines


def executable() -> Path:
    """Select only the bundled worker or this checkout's Cargo release output."""
    name = "telemetry-core.exe" if sys.platform == "win32" else "telemetry-core"
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "native" / name
    return Path(__file__).resolve().parents[1] / "target" / "release" / name


def inspect_capture(text: str, limit: int) -> list[dict[str, Any]]:
    """Run one bounded request; reject failures or mismatched result cardinality, never fake success."""
    lines = capture_lines(text)
    if type(limit) is not int or limit not in (32, 128, 4096):
        raise ValueError("Unsupported native payload limit")
    worker = executable()
    if not worker.is_file():
        raise RuntimeError("Native worker missing; run cargo build --release --locked")
    try:
        completed = subprocess.run(
            [str(worker), str(limit)],
            input=text.encode("ascii"),
            capture_output=True,
            timeout=5,
            check=True,
        )
        if len(completed.stdout) > 1_048_576:
            raise RuntimeError("Unexpected worker output size")
        rows = [json.loads(line) for line in completed.stdout.splitlines()]
        if len(rows) != len(lines) or any(
            not isinstance(row, dict)
            or set(row) != {"code", "header", "actual_size", "payload_hex"}
            for row in rows
        ):
            raise RuntimeError("Unexpected worker result contract")
        return rows
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError) as error:
        raise RuntimeError(
            "Local native parser unavailable or returned invalid evidence"
        ) from error
