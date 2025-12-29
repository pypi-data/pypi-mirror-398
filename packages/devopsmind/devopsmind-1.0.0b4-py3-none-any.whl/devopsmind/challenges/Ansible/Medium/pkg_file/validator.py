#!/usr/bin/env python3
import yaml
import os

def find_task(tasks, module):
    return any(module in task for task in tasks)

def validate():
    if not os.path.exists("playbook.yml"):
        return False, "playbook.yml missing."

    try:
        with open("playbook.yml") as f:
            plays = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML: {e}"

    if not isinstance(plays, list) or not plays:
        return False, "playbook.yml must contain at least one play."

    tasks = plays[0].get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        return False, "Play must contain tasks."

    # Check package installation
    pkg_task = [t for t in tasks if "package" in t or "apt" in t or "yum" in t]
    if not pkg_task:
        return False, "No package installation task found."

    # Look for 'tree'
    pkg_ok = False
    for t in pkg_task:
        mod = list(t.keys())[0]
        pkgname = t[mod].get("name")
        if pkgname == "tree":
            pkg_ok = True
    if not pkg_ok:
        return False, "Package installation task must install 'tree'."

    # Check file creation
    copy_task = [t for t in tasks if "copy" in t]
    if not copy_task:
        return False, "No copy task found."

    correct = False
    for t in copy_task:
        if t["copy"].get("dest") == "/tmp/info.txt" and t["copy"].get("content") == "Ansible Works":
            correct = True

    if not correct:
        return False, "copy task must create /tmp/info.txt with content 'Ansible Works'."

    return True, "Medium Ansible playbook is correct!"

