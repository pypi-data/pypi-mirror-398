#!/usr/bin/env python3
import os
import subprocess

def expected_count():
    # Count processes excluding the header line using ps -e
    out = subprocess.check_output(["ps", "-e"], stderr=subprocess.STDOUT).decode().splitlines()
    # First line may be header on some systems; safe way: count lines minus 1 if header exists.
    # But ps -e usually does not include a header. We'll assume each line is a process entry.
    return len(out)

def validate():
    script = "count_procs.sh"
    if not os.path.exists(script):
        return False, "count_procs.sh missing."

    if not os.access(script, os.X_OK):
        return False, "count_procs.sh not executable. Run: chmod +x count_procs.sh"

    try:
        out = subprocess.check_output(["bash", script], stderr=subprocess.STDOUT, timeout=5).decode().strip()
    except subprocess.CalledProcessError as e:
        return False, f"Script execution failed: {e.output.decode().strip()}"
    except Exception as e:
        return False, f"Error running script: {e}"

    if not out.isdigit():
        return False, "Output must be numeric only."

    try:
        actual = expected_count()
    except Exception as e:
        return False, f"Failed to determine expected count: {e}"

    # Allow a +/-2 drift because ps output can vary with ephemeral processes
    got = int(out)
    if abs(got - actual) <= 2:
        return True, f"Correct (reported {got}, expected approx {actual})."
    return False, f"Reported {got} but expected approx {actual}."

