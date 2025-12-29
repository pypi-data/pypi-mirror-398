#!/usr/bin/env python3
import os
import subprocess

def run(cmd):
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()

def file_in_commit(commit, path):
    try:
        content = run(["git", "show", f"{commit}:{path}"])
        return True, content
    except subprocess.CalledProcessError:
        return False, None

def validate():
    # --------------------------------------------------
    # Basic repo check
    # --------------------------------------------------
    if not os.path.isdir(".git"):
        return False, ".git not found."

    # --------------------------------------------------
    # Ensure main branch exists
    # --------------------------------------------------
    try:
        run(["git", "rev-parse", "--verify", "main"])
    except subprocess.CalledProcessError:
        return False, "Branch 'main' does not exist."

    # --------------------------------------------------
    # Validate login.txt exists in main commit
    # --------------------------------------------------
    present, content = file_in_commit("main", "login.txt")
    if not present:
        return False, (
            "login.txt not present on main. "
            "Make sure you squash-merged feature/login into main."
        )

    if content.strip() != "login implemented":
        return False, "login.txt content on main must be exactly: login implemented"

    # --------------------------------------------------
    # Validate squash commit message (HEAD of main)
    # --------------------------------------------------
    try:
        msg = run(["git", "log", "-1", "--pretty=%s", "main"])
    except subprocess.CalledProcessError:
        return False, "Failed to read the latest commit message on main."

    if "Add auth feature" not in msg:
        return False, (
            "The squash commit on main must contain the substring: "
            "'Add auth feature'"
        )

    # --------------------------------------------------
    # Ensure no merge commits exist on main
    # --------------------------------------------------
    try:
        revs = run(["git", "rev-list", "--parents", "main"])
    except subprocess.CalledProcessError:
        return False, "Failed to inspect commit history on main."

    for line in revs.splitlines():
        parts = line.split()
        if len(parts) > 2:
            return False, (
                "Found a merge commit on main. "
                "History must remain linear after squash-merge."
            )

    return True, "Squash-merge validated: clean history and correct commit."

if __name__ == "__main__":
    ok, msg = validate()
    print(msg)
    exit(0 if ok else 1)
