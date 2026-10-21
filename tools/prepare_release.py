"""Fail-closed draft release preparation by Jason Stys.

Function: main. Variables: version, sha, repository, workflow runs. Index: docs/CODE_INDEX.md.
Only the exact current commit's successful Validation and CodeQL runs authorize packaging.
"""

import json
import os
import re
import subprocess


def main() -> None:
    """Validate version, require successful exact-commit workflows, create a new draft only."""
    version = os.environ["VERSION"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise SystemExit("Expected digits.digits.digits")
    sha, repository = os.environ["GITHUB_SHA"], os.environ["GITHUB_REPOSITORY"]
    for workflow in ("validate.yml", "codeql.yml"):
        result = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{repository}/actions/workflows/{workflow}/runs?head_sha={sha}&per_page=20",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        runs = json.loads(result.stdout)["workflow_runs"]
        if not runs or runs[0]["conclusion"] != "success":
            raise SystemExit(f"{workflow} has not passed at {sha}")
    subprocess.run(
        [
            "gh",
            "release",
            "create",
            f"v{version}",
            "--repo",
            repository,
            "--target",
            sha,
            "--draft",
            "--title",
            f"CCSDS Telemetry Integrity Lab v{version}",
            "--notes",
            "Unsigned portable telemetry-inspection bundles by Jason Stys. Extract the entire ZIP. Educational restricted packet profile, not a complete CCSDS entity. Structural acceptance does not establish payload integrity/authenticity. No spacecraft/radio/command connection. Verify SHA-256; do not bypass OS warnings. See validation and user guide.",
        ],
        check=True,
        timeout=30,
    )


if __name__ == "__main__":
    main()
