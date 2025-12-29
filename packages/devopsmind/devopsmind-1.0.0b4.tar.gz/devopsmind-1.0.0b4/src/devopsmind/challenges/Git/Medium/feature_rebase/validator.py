#!/usr/bin/env python3
import os
import subprocess

def run(cmd):
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()

def branch_exists(branch):
    out = run(["git", "branch", "--list", branch])
    return bool(out.strip())

def get_commit_parents(rev):
    out = run(["git", "rev-list", "--parents", "-n", "1", rev])
    parts = out.split()
    return parts[1:]  # parents only

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
        return False, ".git directory not found."

    # --------------------------------------------------
    # Branch existence
    # --------------------------------------------------
    if not branch_exists("feature/login"):
        return False, "Branch 'feature/login' not found."

    # --------------------------------------------------
    # Resolve branch tips
    # --------------------------------------------------
    try:
        feature_tip = run(["git", "rev-parse", "feature/login"])
        main_tip = run(["git", "rev-parse", "main"])
    except subprocess.CalledProcessError:
        return False, "Failed to resolve branch tips."

    # --------------------------------------------------
    # Ensure feature commit is not a merge commit
    # --------------------------------------------------
    parents = get_commit_parents(feature_tip)
    if len(parents) != 1:
        return False, (
            "The tip of feature/login is a merge commit. "
            "Rebase the feature branch onto main instead of merging."
        )

    # --------------------------------------------------
    # Ensure feature branch is rebased onto latest main
    # --------------------------------------------------
    try:
        base = run(["git", "merge-base", "feature/login", "main"])
    except subprocess.CalledProcessError:
        return False, "Failed to determine merge-base."

    if base != main_tip:
        return False, "feature/login is not rebased onto the latest main branch."

    # --------------------------------------------------
    # Validate file exists in the FEATURE COMMIT
    # --------------------------------------------------
    present, content = file_in_commit(feature_tip, "login.txt")
    if not present:
        return False, "login.txt is not present in the feature/login commit."

    if content.strip() != "login implemented":
        return False, "login.txt content must be exactly: login implemented"

    return True, "Feature branch rebased correctly onto main."

if __name__ == "__main__":
    ok, msg = validate()
    print(msg)
    exit(0 if ok else 1)
