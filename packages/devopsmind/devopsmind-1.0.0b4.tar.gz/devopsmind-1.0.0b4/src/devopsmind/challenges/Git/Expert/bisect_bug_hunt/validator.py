#!/usr/bin/env python3
import os
import subprocess

EXPECTED_HASH_FILE = "bug_commit.txt"

def run(cmd):
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()

def validate():
    if not os.path.isdir(".git"):
        return False, ".git directory not found."

    if not os.path.exists(EXPECTED_HASH_FILE):
        return False, "bug_commit.txt missing."

    with open(EXPECTED_HASH_FILE) as f:
        commit_hash = f.read().strip()

    if not commit_hash:
        return False, "bug_commit.txt is empty."

    # Validate commit exists
    try:
        run(["git", "cat-file", "-e", f"{commit_hash}^{{commit}}"])
    except subprocess.CalledProcessError:
        return False, "Commit hash in bug_commit.txt does not exist."

    # Ensure commit is reachable
    try:
        run(["git", "merge-base", "--is-ancestor", commit_hash, "HEAD"])
    except subprocess.CalledProcessError:
        return False, "Commit hash is not reachable from HEAD."

    return True, "Git Expert challenge passed!"
