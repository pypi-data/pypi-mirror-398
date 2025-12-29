#!/usr/bin/env python3
import os, yaml

def validate():
    if not os.path.exists("deployment.yaml"):
        return False, "deployment.yaml missing."

    try:
        with open("deployment.yaml") as f:
            d = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML: {e}"

    if d.get("apiVersion") != "apps/v1":
        return False, "apiVersion must be apps/v1."

    if d.get("kind") != "Deployment":
        return False, "Kind must be Deployment."

    if d.get("metadata", {}).get("name") != "web-deploy":
        return False, "metadata.name must be web-deploy."

    spec = d.get("spec", {})
    if spec.get("replicas") != 3:
        return False, "replicas must be 3."

    tmpl = spec.get("template", {})
    containers = tmpl.get("spec", {}).get("containers", [])
    if not containers:
        return False, "Deployment must define containers."

    c = containers[0]
    if c.get("name") != "web":
        return False, "Container name must be web."

    if c.get("image") != "nginx:1.21":
        return False, "Container image must be nginx:1.21."

    return True, "Deployment manifest is correct!"

