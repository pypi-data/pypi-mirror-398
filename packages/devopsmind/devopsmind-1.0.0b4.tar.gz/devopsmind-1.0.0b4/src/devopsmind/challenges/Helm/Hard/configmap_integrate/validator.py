#!/usr/bin/env python3
import os, yaml

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def validate():
    values_path = "mychart/values.yaml"
    cm_path = "mychart/templates/configmap.yaml"
    dep_path = "mychart/templates/deployment.yaml"

    # Required files
    for p in [values_path, cm_path, dep_path]:
        if not os.path.exists(p):
            return False, f"{p} missing."

    # Validate values.yaml
    try:
        vals = load_yaml(values_path)
    except Exception as e:
        return False, f"Invalid YAML in values.yaml: {e}"

    if vals.get("config", {}).get("message") != "Hello from Helm":
        return False, "values.yaml must define config.message = 'Hello from Helm'."

    # Validate configmap.yaml template content (must contain template placeholders)
    with open(cm_path) as f:
        cm_content = f.read()

    if "{{ .Chart.Name }}-config" not in cm_content:
        return False, "ConfigMap name must use {{ .Chart.Name }}-config."

    if "{{ .Values.config.message }}" not in cm_content:
        return False, "ConfigMap data.message must use {{ .Values.config.message }}."

    # Validate deployment.yaml for volumes + mounts
    try:
        dep = load_yaml(dep_path)
    except Exception as e:
        return False, f"Invalid YAML in deployment.yaml: {e}"

    spec = dep.get("spec", {}).get("template", {}).get("spec", {})

    volumes = spec.get("volumes", [])
    mounts = spec.get("containers", [{}])[0].get("volumeMounts", [])

    vol_ok = any(
        v.get("name") == "cfg" and v.get("configMap", {}).get("name") == "{{ .Chart.Name }}-config"
        for v in volumes
    )

    mount_ok = any(
        m.get("name") == "cfg" and m.get("mountPath") == "/config"
        for m in mounts
    )

    if not vol_ok:
        return False, "Deployment must define a volume referencing ConfigMap {{ .Chart.Name }}-config."

    if not mount_ok:
        return False, "Deployment must define a volumeMount with mountPath=/config and name=cfg."

    return True, "Hard Helm chart validation passed! ConfigMap integration correct."

