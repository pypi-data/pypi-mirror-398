#!/usr/bin/env python3
import os
import subprocess

def validate():
    script = "readfile.py"
    if not os.path.exists(script):
        return False, "readfile.py is missing."

    testfile = "notes.txt"
    with open(testfile, "w") as f:
        f.write("Hello File\n")

    try:
        out = subprocess.check_output(
            ["python3", script, testfile],
            stderr=subprocess.STDOUT
        ).decode()
    except subprocess.CalledProcessError:
        return False, "Script exited with non-zero code. It must print file contents."

    if out == "Hello File\n":
        return True, "readfile.py works correctly."
    else:
        return False, f"Unexpected output: {repr(out)}"

