"""Actual frozen-executable export and loopback smoke test by Jason Stys.

Functions: main, read_output. Variables: process, queue, temporary output, HTTP responses.
Line inventory: docs/CODE_INDEX.md. Starts/stops only the explicitly supplied owned bundle.
"""

import json

if __package__:
    from .release_contract import require
else:
    from release_contract import require
import queue
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path


def main(executable: Path) -> None:
    """Verify packaged packetlab/resources, health, scenario API and real built HTML/JS."""
    executable = executable.resolve(strict=True)
    for notice in (
        "_internal/licenses/project/LICENSE",
        "_internal/licenses/python/PYTHON.txt",
        "_internal/licenses/pyinstaller/COPYING.txt",
        "_internal/licenses/rust/COPYRIGHT-library.html",
        "_internal/licenses/rust/RUST-MIT.txt",
        "_internal/licenses/rust/RUST-APACHE.txt",
    ):
        require((executable.parent / notice).is_file(), "Missing packaged native runtime notice")
    with tempfile.TemporaryDirectory(prefix="packetlab-smoke-") as temporary:
        output = Path(temporary) / "evidence.json"
        subprocess.run(
            [str(executable), "export", "--scenario", "nominal", "--output", str(output)],
            check=True,
            timeout=30,
        )
        require(
            json.loads(output.read_bytes())["provenance"]["format"]
            == "CCSDS 133.0-B-2 restricted telemetry profile",
            "Legacy native acceptance condition failed",
        )
    process = subprocess.Popen(
        [str(executable), "serve", "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    lines: queue.Queue[str] = queue.Queue()

    def read_output() -> None:
        """Read child stdout without a blocking readline in the timeout-owning main thread."""
        require(process.stdout is not None, "Legacy native acceptance condition failed")
        for line in process.stdout:
            lines.put(line.strip())

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    try:
        url = ""
        for _ in range(5):
            line = lines.get(timeout=15)
            if line.startswith("http://127.0.0.1:"):
                url = line
                break
        require(url, "Frozen server did not announce a loopback URL")
        with urllib.request.urlopen(url + "api/health", timeout=5) as response:
            require(
                json.loads(response.read())["status"] == "ok",
                "Legacy native acceptance condition failed",
            )
        with urllib.request.urlopen(url, timeout=5) as response:
            html = response.read().decode()
            require(
                "CCSDS Telemetry Integrity Lab" in html and "/assets/" in html,
                "Legacy native acceptance condition failed",
            )
        with urllib.request.urlopen(url + "api/run?scenario=sequence-gap", timeout=5) as response:
            require(
                json.loads(response.read())["totals"]["review"] == 1,
                "Legacy native acceptance condition failed",
            )
        print("Frozen app: packetlab export, web assets, health and scenario API passed")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        reader.join(timeout=3)
        if process.stdout:
            process.stdout.close()


if __name__ == "__main__":
    main(Path(sys.argv[1]))
