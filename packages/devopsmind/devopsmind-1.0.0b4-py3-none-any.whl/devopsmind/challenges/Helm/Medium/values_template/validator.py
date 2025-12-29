#!/usr/bin/env python3
import os, yaml

def validate():
    values_path = "mychart/values.yaml"
    tpl_path = "mychart/templates/deployment.yaml"

    if not os.path.exists(values_path):
        return False, "values.yaml missing."

    if not os.path.exists(tpl_path):
        return False, "templates/deployment.yaml missing."

    # Check values.yaml
    try:
        with open(values_path) as f:
            vals = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML in values.yaml: {e}"

    if vals.get("image") != "nginx:alpine":
        return False, "values.yaml must define image: nginx:alpine."

    # Check template for variables
    with open(tpl_path) as f:
        content = f.read()

    if "{{ .Values.image }}" not in content:
        return False, "deployment.yaml must use {{ .Values.image }}."

    if "{{ .Chart.Name }}-deploy" not in content:
        return False, "Deployment name must use {{ .Chart.Name }}-deploy."

    return True, "Medium Helm chart templating looks correct!"

