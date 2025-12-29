#!/usr/bin/env python3
import os
import yaml

def validate():
    path = "deployment.yaml"

    if not os.path.exists(path):
        return False, "deployment.yaml missing."

    try:
        d = yaml.safe_load(open(path))
    except Exception as e:
        return False, f"Invalid YAML: {e}"

    if d.get("kind") != "Deployment":
        return False, "Must define a Deployment."

    if d.get("metadata", {}).get("name") != "resource-deploy":
        return False, "Deployment name must be resource-deploy."

    if d.get("spec", {}).get("replicas") != 2:
        return False, "replicas must be 2."

    containers = d.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
    if not containers:
        return False, "Deployment must define containers."

    c = containers[0]
    if c.get("name") != "app":
        return False, "Container name must be app."
    if c.get("image") != "nginx:alpine":
        return False, "Container image must be nginx:alpine."

    resources = c.get("resources", {})
    req = resources.get("requests", {})
    lim = resources.get("limits", {})

    if req.get("cpu") != "100m" or req.get("memory") != "128Mi":
        return False, "CPU/memory requests incorrect."

    if lim.get("cpu") != "500m" or lim.get("memory") != "256Mi":
        return False, "CPU/memory limits incorrect."

    return True, "Kubernetes Master challenge passed!"
