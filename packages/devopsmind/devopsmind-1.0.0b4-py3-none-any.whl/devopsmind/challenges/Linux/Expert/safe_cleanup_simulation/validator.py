#!/usr/bin/env python3
import subprocess
import os

EXPECTED = [
    "cache.tmp",
    "session.tmp",
]

def validate(context=None):
    script = "cleanup.sh"

    if not os.path.exists(script):
        return False, "cleanup.sh missing."

    if not os.access(script, os.X_OK):
        return False, "cleanup.sh must be executable."

    try:
        out = subprocess.check_output(
            ["bash", script, "--dry-run"],
            text=True,
            timeout=5
        ).strip().splitlines()
    except Exception as e:
        return False, f"Script failed: {e}"

    if out != EXPECTED:
        return False, f"Expected {EXPECTED}, got {out}"

    return True, "Linux Expert challenge passed!"
