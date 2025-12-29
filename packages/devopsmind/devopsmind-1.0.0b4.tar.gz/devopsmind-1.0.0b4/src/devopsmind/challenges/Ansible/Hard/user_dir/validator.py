#!/usr/bin/env python3
import yaml
import os

def validate():
    if not os.path.exists("playbook.yml"):
        return False, "playbook.yml missing."

    try:
        with open("playbook.yml") as f:
            plays = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML: {e}"

    if not isinstance(plays, list) or not plays:
        return False, "Playbook must contain a list of plays."

    tasks = plays[0].get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        return False, "Play must contain tasks."

    user_ok = False
    dir_ok = False

    for t in tasks:
        if "user" in t:
            if t["user"].get("name") == "deploy":
                user_ok = True

        if "file" in t:
            f = t["file"]
            if (
                f.get("path") == "/opt/deploy"
                and f.get("state") == "directory"
                and f.get("owner") == "deploy"
                and f.get("mode") in ("0755", 755)
            ):
                dir_ok = True

    if not user_ok:
        return False, "User task for 'deploy' missing."

    if not dir_ok:
        return False, "Directory task for /opt/deploy missing or incorrect."

    return True, "Hard Ansible playbook is correct and idempotent!"

