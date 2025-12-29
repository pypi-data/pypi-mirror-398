#!/usr/bin/env python3
import os
import re

def validate():
    if not os.path.exists("Dockerfile"):
        return False, "Dockerfile missing."
    if not os.path.exists("app.py"):
        return False, "app.py required."
    if not os.path.exists("requirements.txt"):
        return False, "requirements.txt required."

    with open("Dockerfile") as f:
        content = f.read()

    # Must contain two FROM lines (multi-stage)
    if content.count("FROM") < 2:
        return False, "Dockerfile must use multi-stage build with at least two FROM statements."

    # Check stage1 has pip install
    stage1_ok = "pip install" in content or "pip3 install" in content
    if not stage1_ok:
        return False, "Builder stage must install dependencies using pip install."

    # Ensure final stage runs python app.py
    if not re.search(r'(CMD|ENTRYPOINT).*python.*app.py', content):
        return False, "Final stage must run python app.py."

    return True, "Multi-stage Dockerfile validated!"

