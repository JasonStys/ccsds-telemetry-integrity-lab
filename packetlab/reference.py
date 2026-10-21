"""Independent arithmetic/structural Python reference by Jason Stys.

Functions: inspect_record, capture_lines. Variables: header words, quotient/remainder
fields and strict byte/record limits. Not a fallback for a missing Rust worker.
Exact definitions/arguments: docs/CODE_INDEX.md.
"""

import re
from typing import Any

MAX_CAPTURE = 131_072
MAX_RECORDS = 128


def capture_lines(text: str) -> list[str]:
    """Respect explicit newline-delimited lab boundaries; no raw-byte resynchronization claim."""
    if not text.isascii() or len(text) > MAX_CAPTURE:
        raise ValueError("Capture must be ASCII and at most 128 KiB")
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    if len(lines) > MAX_RECORDS:
        raise ValueError("Capture exceeds 128 records")
    return [line.removesuffix("\r") for line in lines]


def inspect_record(text: str, limit: int) -> dict[str, Any]:
    """Decode with division/remainder, independent of Rust's masks and byte conversion code."""
    result: dict[str, Any] = {"code": "", "header": None, "actual_size": None, "payload_hex": ""}
    if len(text) > 8204:
        return {**result, "code": "record-too-large"}
    if len(text) % 2 or not re.fullmatch("[0-9a-fA-F]*", text):
        return {**result, "code": "invalid-hex"}
    raw = bytes.fromhex(text)
    result["actual_size"] = len(raw)
    if len(raw) < 6:
        return {**result, "code": "truncated-header"}
    first, second, length = (int.from_bytes(raw[index : index + 2], "big") for index in (0, 2, 4))
    header = {
        "version": first // 8192,
        "packet_type": first // 4096 % 2,
        "secondary": first // 2048 % 2,
        "apid": first % 2048,
        "flags": second // 16384,
        "sequence": second % 16384,
        "data_length": length,
        "expected_size": length + 7,
    }
    result["header"] = header
    if not 1 <= limit <= 4096:
        code = "invalid-profile-limit"
    elif header["version"] != 0:
        code = "unsupported-version"
    elif len(raw) != length + 7:
        code = "length-mismatch"
    elif length + 1 > limit:
        code = "profile-payload-limit"
    elif header["packet_type"] != 0:
        code = "unsupported-packet-type"
    elif header["secondary"]:
        code = "unsupported-secondary-header"
    elif header["flags"] != 3:
        code = "unsupported-segmentation"
    else:
        code = "accepted"
        result["payload_hex"] = raw[6:].hex()
    return {**result, "code": code}
