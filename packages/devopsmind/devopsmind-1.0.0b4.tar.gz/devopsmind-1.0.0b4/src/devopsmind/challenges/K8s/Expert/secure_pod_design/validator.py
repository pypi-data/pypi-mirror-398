#!/usr/bin/env python3
import os
import yaml

def validate():
    path = "pod.yaml"

    if not os.path.exists(path):
        return False, "pod.yaml missing."

    try:
        pod = yaml.safe_load(open(path))
    except Exception as e:
        return False, f"Invalid YAML: {e}"

    if pod.get("kind") != "Pod":
        return False, "Must define a Pod."

    if pod.get("metadata", {}).get("name") != "secure-pod":
        return False, "Pod name must be secure-pod."

    spec = pod.get("spec", {})
    containers = spec.get("containers", [])
    if not containers:
        return False, "Pod must define containers."

    c = containers[0]
    if c.get("image") != "nginx:alpine":
        return False, "Container image must be nginx:alpine."

    sc = c.get("securityContext", {}) or spec.get("securityContext", {})

    if sc.get("runAsNonRoot") is not True:
        return False, "runAsNonRoot must be true."
    if sc.get("runAsUser") != 1000:
        return False, "runAsUser must be 1000."
    if sc.get("allowPrivilegeEscalation") is not False:
        return False, "allowPrivilegeEscalation must be false."
    if sc.get("readOnlyRootFilesystem") is not True:
        return False, "readOnlyRootFilesystem must be true."

    return True, "Kubernetes Expert challenge passed!"
