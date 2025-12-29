#!/usr/bin/env python3
import os
import re

def validate():
    if not os.path.exists("Dockerfile"):
        return False, "Dockerfile missing."

    with open("Dockerfile") as f:
        content = f.read()

    # Multi-stage check
    if content.count("FROM") < 2:
        return False, "Dockerfile must use multi-stage build."

    # Builder stage
    if not re.search(r'pip\s+install', content):
        return False, "Builder stage must install dependencies."

    # Non-root user
    if not re.search(r'adduser|useradd', content):
        return False, "Non-root user must be created."

    if not re.search(r'USER\s+', content):
        return False, "Dockerfile must switch to non-root USER."

    # CMD
    if not re.search(r'CMD\s+\["python",\s*"app\.py"\]', content):
        return False, "CMD must run python app.py."

    # Security check
    if "requirements.txt" in re.findall(r'COPY\s+.*', content)[-1]:
        return False, "requirements.txt must not be copied into final stage."

    return True, "Docker Expert challenge passed!"
