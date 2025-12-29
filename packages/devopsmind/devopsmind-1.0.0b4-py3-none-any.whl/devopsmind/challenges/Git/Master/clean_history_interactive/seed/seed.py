#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

def run(cmd):
    subprocess.run(cmd, check=True)

def seed():
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)

    # Clean any existing repo
    if (root / ".git").exists():
        subprocess.run(["rm", "-rf", ".git"])

    # Init repo
    run(["git", "init"])
    run(["git", "branch", "-m", "main"])

    # Base commit on main
    with open("core.py", "w") as f:
        f.write("def core(): pass\n")
    run(["git", "add", "core.py"])
    run(["git", "commit", "-m", "Initial core implementation"])

    # Feature branch with messy history
    run(["git", "checkout", "-b", "feature/refactor"])

    with open("core.py", "a") as f:
        f.write("# refactor step 1\n")
    run(["git", "commit", "-am", "WIP refactor"])

    with open("core.py", "a") as f:
        f.write("# fix typo\n")
    run(["git", "commit", "-am", "Fix typo"])

    with open("core.py", "a") as f:
        f.write("# cleanup\n")
    run(["git", "commit", "-am", "Cleanup code"])

    run(["git", "checkout", "main"])

if __name__ == "__main__":
    seed()
