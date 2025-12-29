#!/usr/bin/env python3
import os
import yaml

def validate():
    if not os.path.exists("pod.yaml"):
        return False, "pod.yaml missing."

    try:
        with open("pod.yaml") as f:
            pod = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML: {e}"

    if pod.get("apiVersion") != "v1":
        return False, "apiVersion must be v1."

    if pod.get("kind") != "Pod":
        return False, "kind must be Pod."

    meta = pod.get("metadata", {})
    if meta.get("name") != "hello-pod":
        return False, "Pod name must be hello-pod."

    spec = pod.get("spec", {})
    containers = spec.get("containers", [])
    if not isinstance(containers, list) or len(containers) != 1:
        return False, "Pod must have exactly one container."

    c = containers[0]
    if c.get("name") != "web":
        return False, "Container name must be web."

    if c.get("image") != "nginx":
        return False, "Container image must be nginx."

    return True, "Basic Pod manifest is correct!"

