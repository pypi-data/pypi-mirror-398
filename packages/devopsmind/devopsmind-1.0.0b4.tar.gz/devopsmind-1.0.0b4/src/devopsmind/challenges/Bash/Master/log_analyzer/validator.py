#!/usr/bin/env python3
import subprocess
import os

EXPECTED = [
    "INFO: 2",
    "WARN: 1",
    "ERROR: 2",
]

def validate(context=None):
    script = "analyze_logs.sh"

    if not os.path.exists(script):
        return False, "analyze_logs.sh missing."

    if not os.access(script, os.X_OK):
        return False, "analyze_logs.sh must be executable."

    try:
        output = subprocess.check_output(
            ["bash", script],
            text=True,
            timeout=5
        ).strip().splitlines()
    except Exception as e:
        return False, f"Script failed: {e}"

    if output != EXPECTED:
        return False, f"Output mismatch.\nExpected: {EXPECTED}\nGot: {output}"

    return True, "Bash Master challenge passed!"
