#!/usr/bin/env python3
import os
import subprocess

def run(cmd):
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()

def validate():
    if not os.path.isdir(".git"):
        return False, ".git directory not found."

    # Ensure branch exists
    try:
        run(["git", "rev-parse", "--verify", "feature/refactor"])
    except subprocess.CalledProcessError:
        return False, "Branch 'feature/refactor' does not exist."

    # Get commits on feature/refactor
    commits = run([
        "git", "rev-list", "--first-parent", "feature/refactor"
    ]).splitlines()

    if len(commits) != 1:
        return False, (
            "feature/refactor must contain exactly ONE commit after history rewrite."
        )

    commit = commits[0]

    # Ensure single parent (not merge commit)
    parents = run([
        "git", "rev-list", "--parents", "-n", "1", commit
    ]).split()

    if len(parents) != 2:
        return False, "The commit must have exactly one parent (no merge commits)."

    # Validate commit message
    msg = run([
        "git", "log", "-1", "--pretty=%s", "feature/refactor"
    ])

    if msg != "Refactor core logic":
        return False, (
            "Final commit message must be exactly: 'Refactor core logic'"
        )

    return True, "Master Git challenge passed: history cleaned perfectly."

if __name__ == "__main__":
    ok, msg = validate()
    print(msg)
    exit(0 if ok else 1)
