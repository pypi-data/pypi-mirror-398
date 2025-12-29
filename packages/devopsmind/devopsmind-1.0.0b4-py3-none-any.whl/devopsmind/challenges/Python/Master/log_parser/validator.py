import subprocess
import os

EXPECTED = [
    "INFO: 2",
    "ERROR: 2",
    "WARN: 1",
]

def validate(context=None):
    script = "log_parser.py"

    if not os.path.exists(script):
        return False, "log_parser.py missing."

    try:
        output = subprocess.check_output(
            ["python3", script],
            text=True,
            timeout=5
        ).strip().splitlines()
    except Exception as e:
        return False, f"Script failed: {e}"

    if output != EXPECTED:
        return False, f"Output mismatch.\nExpected:\n{EXPECTED}\nGot:\n{output}"

    return True, "Log summary generated correctly."
