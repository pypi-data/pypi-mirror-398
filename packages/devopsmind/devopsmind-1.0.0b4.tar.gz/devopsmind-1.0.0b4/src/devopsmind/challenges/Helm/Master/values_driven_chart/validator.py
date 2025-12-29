#!/usr/bin/env python3
import os
import yaml

def validate():
    values_path = "mychart/values.yaml"
    deploy_path = "mychart/templates/deployment.yaml"

    if not os.path.exists(values_path):
        return False, "values.yaml missing."
    if not os.path.exists(deploy_path):
        return False, "deployment.yaml missing."

    try:
        values = yaml.safe_load(open(values_path))
    except Exception as e:
        return False, f"Invalid YAML in values.yaml: {e}"

    if values.get("replicaCount") != 3:
        return False, "replicaCount must be 3."

    image = values.get("image", {})
    if image.get("repository") != "nginx" or image.get("tag") != "alpine":
        return False, "image.repository must be nginx and tag alpine."

    content = open(deploy_path).read()

    if "{{ .Values.replicaCount }}" not in content:
        return False, "replicas must use {{ .Values.replicaCount }}."

    if "{{ .Values.image.repository }}:{{ .Values.image.tag }}" not in content:
        return False, "Image must be templated from values.yaml."

    if "{{ .Chart.Name }}-deploy" not in content:
        return False, "Deployment name must use {{ .Chart.Name }}-deploy."

    return True, "Helm Master challenge passed!"
