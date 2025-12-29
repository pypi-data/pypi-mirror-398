#!/usr/bin/env python3
import os
import yaml
import re

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def validate():
    defaults = "roles/web/defaults/main.yml"
    tasks = "roles/web/tasks/main.yml"

    if not os.path.exists(defaults):
        return False, "roles/web/defaults/main.yml missing."
    if not os.path.exists(tasks):
        return False, "roles/web/tasks/main.yml missing."

    try:
        defaults_data = load_yaml(defaults)
    except Exception as e:
        return False, f"Invalid YAML in defaults: {e}"

    if defaults_data.get("app_port") != 8080:
        return False, "app_port must be defined as 8080 in defaults."

    try:
        tasks_data = load_yaml(tasks)
    except Exception as e:
        return False, f"Invalid YAML in tasks: {e}"

    if not isinstance(tasks_data, list) or not tasks_data:
        return False, "tasks/main.yml must contain at least one task."

    task = tasks_data[0]
    if "debug" not in task:
        return False, "Task must use debug module."

    msg = task["debug"].get("msg", "")
    if "{{ app_port }}" not in msg:
        return False, "Task must reference variable {{ app_port }}."

    return True, "Ansible Master challenge passed!"
