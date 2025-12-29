#!/usr/bin/env python3
import os
import subprocess

def validate():
    script = "echo_hello.sh"
    if not os.path.exists(script):
        return False, "echo_hello.sh is missing."

    if not os.access(script, os.X_OK):
        return False, "echo_hello.sh is not executable. Run: chmod +x echo_hello.sh"

    try:
        out = subprocess.check_output(["bash", script], stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        return False, f"Script failed to run: {e.output.decode().strip()}"

    # Accept a single trailing newline
    if out.strip() == "Hello DevOpsMind":
        return True, "Correct output!"
    return False, f"Unexpected output: {repr(out)}"

