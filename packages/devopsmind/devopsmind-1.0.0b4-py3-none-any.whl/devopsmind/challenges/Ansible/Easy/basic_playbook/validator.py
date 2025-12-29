#!/usr/bin/env python3
import yaml
import os

def validate():
    if not os.path.exists("playbook.yml"):
        return False, "playbook.yml missing."

    try:
        with open("playbook.yml") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML: {e}"

    if not isinstance(data, list) or len(data) == 0:
        return False, "playbook.yml must be a list of plays."

    play = data[0]
    tasks = play.get("tasks", [])
    if not tasks:
        return False, "Playbook must contain at least one task."

    task = tasks[0]
    if "debug" not in task:
        return False, "Task must use debug module."

    msg = task["debug"].get("msg", "")
    if msg != "Hello Ansible":
        return False, "Debug message must be exactly: Hello Ansible"

    return True, "Basic playbook looks good!"

