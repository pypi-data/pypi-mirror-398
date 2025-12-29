#!/usr/bin/env python3
import subprocess
import os

EXPECTED = [
    "200: 3",
    "404: 1",
    "500: 1",
]

def validate(context=None):
    script = "metrics.sh"

    if not os.path.exists(script):
        return False, "metrics.sh missing."

    if not os.access(script, os.X_OK):
        return False, "metrics.sh must be executable."

    try:
        out = subprocess.check_output(
            ["bash", script],
            text=True,
            timeout=5
        ).strip().splitlines()
    except Exception as e:
        return False, f"Script failed: {e}"

    if out != EXPECTED:
        return False, f"Output mismatch. Expected {EXPECTED}, got {out}"

    return True, "Linux Master challenge passed!"
