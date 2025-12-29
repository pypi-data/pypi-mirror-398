#!/usr/bin/env python3
import os

def validate():
    if not os.path.exists("Dockerfile"):
        return False, "Dockerfile missing."

    with open("Dockerfile") as f:
        content = f.read()

    if "FROM python:3.10-slim" not in content:
        return False, "Dockerfile must start from python:3.10-slim."

    # check simple command
    if ("CMD" not in content) and ("ENTRYPOINT" not in content):
        return False, "Dockerfile must define CMD or ENTRYPOINT."

    if "Hello Docker" not in content:
        return False, "Container must print 'Hello Docker'."

    return True, "Basic Dockerfile is correct!"

