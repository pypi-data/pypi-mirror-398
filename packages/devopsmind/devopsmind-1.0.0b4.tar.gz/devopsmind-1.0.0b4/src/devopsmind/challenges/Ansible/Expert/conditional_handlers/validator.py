
---

## 📄 `validator.py`
```python
#!/usr/bin/env python3
import os
import yaml

def validate():
    path = "playbook.yml"
    if not os.path.exists(path):
        return False, "playbook.yml missing."

    try:
        data = yaml.safe_load(open(path))
    except Exception as e:
        return False, f"Invalid YAML: {e}"

    if not isinstance(data, list) or not data:
        return False, "playbook.yml must contain a list of plays."

    play = data[0]
    tasks = play.get("tasks", [])
    handlers = play.get("handlers", [])

    if not tasks:
        return False, "No tasks defined."
    if not handlers:
        return False, "No handlers defined."

    task = tasks[0]
    if "when" not in task:
        return False, "Task must include a when condition."

    if task.get("notify") != "restart app":
        return False, "Task must notify handler 'restart app'."

    handler_names = [h.get("name") for h in handlers]
    if "restart app" not in handler_names:
        return False, "Handler 'restart app' missing."

    handler = next(h for h in handlers if h.get("name") == "restart app")
    if "debug" not in handler:
        return False, "Handler must use debug module."

    return True, "Ansible Expert challenge passed!"
