#!/usr/bin/env python3
import os
import subprocess
import sys

def run(cmd):
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()

def validate():
    if not os.path.isdir(".git"):
        return False, ".git directory not found. Run: git init"

    if not os.path.exists("README.md"):
        return False, "README.md missing."

    with open("README.md") as f:
        content = f.read().strip()
    if content != "DevOpsMind Git":
        return False, "README.md content must be exactly: DevOpsMind Git"

    try:
        msg = run(["git", "log", "-1", "--pretty=%B"])
    except subprocess.CalledProcessError as e:
        return False, f"Failed to read git log: {e.output.decode().strip()}"

    if msg.strip() != "Initial commit":
        return False, f"Latest commit message must be 'Initial commit' (got: {msg.strip()!r})"

    return True, "Repository initialized and committed correctly."

