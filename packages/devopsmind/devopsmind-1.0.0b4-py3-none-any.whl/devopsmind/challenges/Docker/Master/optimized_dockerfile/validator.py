#!/usr/bin/env python3
import os
import re

def validate():
    if not os.path.exists("Dockerfile"):
        return False, "Dockerfile missing."

    with open("Dockerfile") as f:
        content = f.read()

    # Base image
    if "FROM python:3.10-slim" not in content:
        return False, "Base image must be python:3.10-slim."

    # Workdir
    if not re.search(r'WORKDIR\s+/app', content):
        return False, "WORKDIR /app must be defined."

    # Copy rule
    if not re.search(r'COPY\s+app\.py\s+/app', content):
        return False, "Must COPY only app.py into /app."

    if re.search(r'COPY\s+\.\s+', content):
        return False, "COPY . . is not allowed."

    # CMD
    if not re.search(r'CMD\s+\["python",\s*"app\.py"\]', content):
        return False, "CMD must run python app.py."

    return True, "Docker Master challenge passed!"
