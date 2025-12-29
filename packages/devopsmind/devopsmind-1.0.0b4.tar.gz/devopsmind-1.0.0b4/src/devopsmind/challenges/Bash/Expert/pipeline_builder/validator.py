#!/usr/bin/env python3
import subprocess
import os

EXPECTED_SUM = "12"

def validate(context=None):
    script = "process_numbers.sh"

    if not os.path.exists(script):
        return False, "process_numbers.sh missing."

    if not os.access(script, os.X_OK):
        return False, "process_numbers.sh must be executable."

    try:
        output = subprocess.check_output(
            ["bash", script],
            text=True,
            timeout=5
        ).strip()
    except subprocess.CalledProcessError:
        return False, "Script failed or exited with non-zero code."

    if output != EXPECTED_SUM:
        return False, f"Expected output {EXPECTED_SUM}, got {output}"

    return True, "Bash Expert challenge passed!"
