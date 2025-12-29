#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path


def run(cmd):
    subprocess.run(cmd, check=True)


def seed():
    # -------------------------------------------------
    # ALWAYS run from challenge root (parent of seed/)
    # -------------------------------------------------
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)

    # Clean up any accidental repo inside seed/
    bad_git = root / "seed" / ".git"
    if bad_git.exists():
        subprocess.run(["rm", "-rf", str(bad_git)])

    # Initialize repository at correct location
    run(["git", "init"])
    run(["git", "branch", "-m", "main"])

    # Commit 1 — good
    with open("app.py", "w") as f:
        f.write("def add(a, b): return a + b\n")
    run(["git", "add", "app.py"])
    run(["git", "commit", "-m", "Add add() function"])

    # Commit 2 — still good
    with open("app.py", "a") as f:
        f.write("def sub(a, b): return a - b\n")
    run(["git", "add", "app.py"])
    run(["git", "commit", "-m", "Add sub() function"])

    # Commit 3 — BUG introduced
    with open("app.py", "r") as f:
        content = f.read().replace("return a + b", "return a - b")
    with open("app.py", "w") as f:
        f.write(content)
    run(["git", "add", "app.py"])
    run(["git", "commit", "-m", "Refactor add logic"])

    # Commit 4 — still broken
    with open("app.py", "a") as f:
        f.write("print(add(2, 2))\n")
    run(["git", "add", "app.py"])
    run(["git", "commit", "-m", "Add debug print"])


if __name__ == "__main__":
    seed()
