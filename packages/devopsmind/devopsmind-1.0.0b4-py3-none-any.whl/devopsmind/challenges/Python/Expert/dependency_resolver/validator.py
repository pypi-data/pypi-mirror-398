import subprocess
import os

DEPS = {
    "build": [],
    "test": ["build"],
    "lint": ["build"],
    "package": ["test", "lint"],
    "deploy": ["package"],
}

def validate(context=None):
    script = "resolve_deps.py"

    if not os.path.exists(script):
        return False, "resolve_deps.py missing."

    try:
        output = subprocess.check_output(
            ["python3", script],
            text=True,
            timeout=5
        ).strip().splitlines()
    except Exception as e:
        return False, f"Script failed: {e}"

    if set(output) != set(DEPS.keys()):
        return False, "Output must include all tasks exactly once."

    position = {task: i for i, task in enumerate(output)}

    for task, deps in DEPS.items():
        for dep in deps:
            if position[dep] >= position[task]:
                return False, f"Dependency order invalid: {task} depends on {dep}"

    return True, "Dependencies resolved in valid order."
